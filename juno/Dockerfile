# Stage 1: Build golang dependencies and binaries
FROM golang:1.23 AS build

# Install build dependencies
RUN apt-get -y update && \
    apt-get -y install   \
		curl             \
		build-essential  \
		git              \
		libjemalloc-dev  \
		libjemalloc2  && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -q -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Set the working directory
WORKDIR /usr/src/

# Download juno from last build with passing CI
# https://github.com/NethermindEth/juno/commit/1862240f8ff8da6f94fb7c2e1a0f062bbe5780ba
RUN git clone https://github.com/NethermindEth/juno.git juno && \
    cd juno                                                  && \
    git checkout 1862240f8ff8da6f94fb7c2e1a0f062bbe5780ba

# Set the compilation directory
WORKDIR /usr/src/juno

# Build the application
RUN make juno

# Stage 2: Build Docker image
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update                                          && \
    apt-get install -y ca-certificates libjemalloc2 busybox && \
    apt-get autoremove -y;                                     \
    apt-get clean;                                             \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /usr/local/bin

# Copy the compiled binary from the builder stage
COPY --from=build /usr/src/juno/build/juno .

# Copies the runner. This is responsible for reading secrets and launching juno
COPY ./juno-runner.sh .
RUN chmod a+x ./juno-runner.sh

# Set the entrypoint
ENTRYPOINT ["/usr/local/bin/juno-runner.sh"]
