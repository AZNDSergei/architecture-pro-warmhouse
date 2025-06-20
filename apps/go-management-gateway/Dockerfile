FROM golang:1.24.4-alpine AS build         

WORKDIR /app
COPY go.* ./
RUN go mod download

COPY . .
RUN go build -o /go-management-gateway ./...

FROM alpine:3.20
COPY --from=build /go-management-gateway /usr/local/bin/
ENTRYPOINT ["go-management-gateway"]
