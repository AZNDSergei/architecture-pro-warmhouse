package main

import (
	"context"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"
	"time"

	"github.com/coreos/go-oidc/v3/oidc"
)

const (
	targetBase    = "http://device-management:80"
	targetBaseOld = "http://legacy-monolith:8082"
	listenAddr    = ":8081"
)

var (
	issuerURL = getEnv("KEYCLOAK_ISSUER_URL", "http://keycloak:8080/realms/iot-realm")
	clientID  = getEnv("KEYCLOAK_CLIENT_ID", "management-gateway")
	proxyAuth = "Bearer " + getEnv("API_KEY", "")
)

var verifier *oidc.IDTokenVerifier

func initOIDC() {
	ctx := context.Background()
	for attempt, wait := 1, 3*time.Second; attempt <= 10; attempt, wait = attempt+1, wait*2 {
		provider, err := oidc.NewProvider(ctx, issuerURL)
		if err == nil {
			verifier = provider.Verifier(&oidc.Config{ClientID: clientID})
			log.Printf("OIDC ready (attempt %d)", attempt)
			return
		}
		log.Printf("OIDC init failed: %v (attempt %d), retry in %s", err, attempt, wait)
		time.Sleep(wait)
	}
	log.Fatalf("OIDC provider init failed after retries")
}
func newProxy(target string) *httputil.ReverseProxy {
	targetURL, err := url.Parse(target)
	if err != nil {
		log.Fatalf("Invalid target: %v", err)
	}
	p := httputil.NewSingleHostReverseProxy(targetURL)

	origDirector := p.Director
	p.Director = func(r *http.Request) {
		origDirector(r)

	}
	return p
}

func authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {

		if r.URL.Path == "/healthz" {
			next.ServeHTTP(w, r)
			return
		}
		/*
			raw := r.Header.Get("Authorization")
			if raw == "" {
				http.Error(w, "missing Authorization header", http.StatusUnauthorized)
				return
			}
			parts := strings.SplitN(raw, " ", 2)
			if len(parts) != 2 || !strings.EqualFold(parts[0], "Bearer") {
				http.Error(w, "invalid Authorization header", http.StatusUnauthorized)
				return
			}

			idToken, err := verifier.Verify(r.Context(), parts[1])
			if err != nil {
				http.Error(w, "invalid or expired token", http.StatusUnauthorized)
				return
			}

			var claims struct {
				Sub   string   `json:"sub"`
				Email string   `json:"email"`
				Roles []string `json:"roles"`
			}
			_ = idToken.Claims(&claims)
		*/
		next.ServeHTTP(w, r)
	})
}

func main() {
	initOIDC()

	proxyV1 := newProxy(targetBaseOld)
	proxyV2 := newProxy(targetBase)

	mux := http.NewServeMux()
	mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("%s %s", r.Method, r.URL.Path)

		switch {
		case strings.HasPrefix(r.URL.Path, "/api/v1.0/"):
			proxyV1.ServeHTTP(w, r)

		case strings.HasPrefix(r.URL.Path, "/api/v2.0/"):
			proxyV2.ServeHTTP(w, r)

		default:
			http.NotFound(w, r)
		}
	})

	log.Printf("Gateway up on %s", listenAddr)
	if err := http.ListenAndServe(listenAddr, authMiddleware(mux)); err != nil {
		log.Fatalf("Gateway crashed: %v", err)
	}
}

func getEnv(key, def string) string {
	if v, ok := os.LookupEnv(key); ok {
		return v
	}
	return def
}
