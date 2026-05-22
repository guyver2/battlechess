# syntax=docker/dockerfile:1

FROM rust:1-bookworm AS builder
WORKDIR /app

COPY Cargo.toml Cargo.lock ./
COPY crates ./crates
COPY migrations ./migrations

RUN cargo build --release -p btch-server

FROM debian:bookworm-slim AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/target/release/btch-server /app/btch-server
COPY static ./static

ENV PORT=3100 \
    DATABASE_URL=sqlite:/data/battlechess.db?mode=rwc

EXPOSE 3100

VOLUME ["/data"]

CMD ["/app/btch-server"]
