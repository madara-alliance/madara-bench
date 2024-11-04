# Stage 1: Build the application
FROM rust:1.80 AS builder
WORKDIR /usr/src/

# Install build dependencies
RUN apt-get -y update &&  \
    apt-get install -y    \
	build-essential   \
	pkg-config        \
	libssl-dev        \
	protobuf-compiler \
	libzstd-dev

# Downloading pathfinder v0.14.3
# https://github.com/eqlabs/pathfinder/tree/release/v0.14.4
RUN git clone https://github.com/eqlabs/pathfinder.git pathfinder && \
    cd pathfinder                                                 && \
    git fetch --tags                                              && \
    git checkout tags/v0.14.4

# Set the compilation directory
WORKDIR /usr/src/pathfinder

# Build the application in release-lto mode
RUN cargo build           \
    --locked              \
    --profile release-lto \
    --package pathfinder  \
    --bin pathfinder

# Stage 2: Create the final runtime image
FROM debian:bookworm-slim AS runner

# Install runtime dependencies
RUN apt-get -y update                                         && \
    apt-get install -y ca-certificates libzstd1 libgmp10 tini && \
    apt-get autoremove -y;                                       \
    apt-get clean;                                               \
	rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 1000 pathfinder                            && \
    useradd                                                      \
        --no-log-init                                            \
        --uid 1000                                               \
        --gid pathfinder                                         \
        --no-create-home pathfinder

# Set the working directory
WORKDIR /usr/local/bin

# Copy the compiled binary from the builder stage
COPY --from=builder /usr/src/pathfinder/target/release-lto/pathfinder .

# Set the entrypoint
CMD ["/usr/local/bin/runner.sh"]
