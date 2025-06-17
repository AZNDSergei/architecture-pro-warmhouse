package main

import (
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"context"

	"github.com/gorilla/mux"
	"github.com/minio/minio-go/v7"
	"github.com/minio/minio-go/v7/pkg/credentials"
)

func main() {
	r := mux.NewRouter()
	r.HandleFunc("/upload", uploadHandler).Methods("POST")

	fmt.Println("Server started on :8080")
	log.Fatal(http.ListenAndServe(":8080", r))
}

func uploadHandler(w http.ResponseWriter, r *http.Request) {
	ctx := context.Background()

	minioClient, err := minio.New("minio:9002", &minio.Options{
		Creds:  credentials.NewStaticV4("minioadmin", "minioadmin", ""),
		Secure: false,
	})
	if err != nil {
		http.Error(w, "Failed to connect to MinIO", http.StatusInternalServerError)
		log.Println("MinIO error:", err)
		return
	}

	bucket := "videos"
	objectName := fmt.Sprintf("stream_%d.mp4", time.Now().Unix())

	// Ensure bucket exists
	exists, err := minioClient.BucketExists(ctx, bucket)
	if err != nil {
		http.Error(w, "MinIO bucket check error", http.StatusInternalServerError)
		return
	}
	if !exists {
		err = minioClient.MakeBucket(ctx, bucket, minio.MakeBucketOptions{})
		if err != nil {
			http.Error(w, "Failed to create bucket", http.StatusInternalServerError)
			return
		}
	}

	// Save to temp file first
	tmpFile, err := os.CreateTemp("", "upload-*.mp4")
	if err != nil {
		http.Error(w, "Failed to create temp file", http.StatusInternalServerError)
		return
	}
	defer os.Remove(tmpFile.Name())

	_, err = io.Copy(tmpFile, r.Body)
	if err != nil {
		http.Error(w, "Failed to read stream", http.StatusInternalServerError)
		return
	}

	// Rewind file
	_, err = tmpFile.Seek(0, io.SeekStart)
	if err != nil {
		http.Error(w, "ailed to rewind file", http.StatusInternalServerError)
		return
	}

	info, err := minioClient.FPutObject(ctx, bucket, objectName, tmpFile.Name(), minio.PutObjectOptions{
		ContentType: "video/mp4",
	})
	if err != nil {
		http.Error(w, "ailed to upload to MinIO", http.StatusInternalServerError)
		log.Println("Upload error:", err)
		return
	}

	log.Printf("Uploaded: %s (%d bytes)\n", info.Key, info.Size)
	w.WriteHeader(http.StatusCreated)
	fmt.Fprintf(w, "Uploaded: %s\n", info.Key)
}
