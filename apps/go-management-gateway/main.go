package main

import (
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"strings"
)

// конечные сервисы
const (
	targetBase      = "http://device-management:80" // v2
	targetBaseOld   = "http://legacy-monolith:8082" // v1
	listenAddr      = ":8081"
	defaultAPIToken = "по необходимости имплементирую"
)

// создаём готовый ReverseProxy c общим Director
func newProxy(target string) *httputil.ReverseProxy {
	targetURL, err := url.Parse(target)
	if err != nil {
		log.Fatalf("Invalid target URL %q: %v", target, err)
	}

	proxy := httputil.NewSingleHostReverseProxy(targetURL)

	origDirector := proxy.Director
	proxy.Director = func(req *http.Request) {
		origDirector(req)
		req.Header.Set("Authorization", "Bearer "+getEnv("API_KEY", defaultAPIToken))
	}

	return proxy
}

func main() {
	proxyV1 := newProxy(targetBaseOld)
	proxyV2 := newProxy(targetBase)

	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		log.Printf("Proxying %s %s", r.Method, r.URL.Path)

		switch {
		case strings.HasPrefix(r.URL.Path, "/api/v1.0/"):
			proxyV1.ServeHTTP(w, r)
		case strings.HasPrefix(r.URL.Path, "/api/v2.0/"):
			proxyV2.ServeHTTP(w, r)
		default:
			http.NotFound(w, r)
		}
	})

	log.Printf("Gateway listening on %s", listenAddr)
	if err := http.ListenAndServe(listenAddr, nil); err != nil {
		log.Fatalf("Server failed: %v", err)
	}
}

// getEnv возвращает значение переменной окружения или запасное
func getEnv(key, fallback string) string {
	if val, ok := os.LookupEnv(key); ok {
		return val
	}
	return fallback
}
