# Stage 1: Build the application
FROM rust:1.78 AS builder

# Install build dependencies
RUN apt-get -y update && \
    apt-get install -y clang git && \
    apt-get autoremove -y; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /usr/src/

# Downloading madara from Sep 12, 2024
# https://github.com/madara-alliance/madara/commit/d45dc388bbb62de8e715014d18f2bca93dfa198e
RUN git clone https://github.com/madara-alliance/madara.git madara && \
    cd madara && \
	git checkout d45dc388bbb62de8e715014d18f2bca93dfa198e

# Installing scarb, new since devnet integration
# Installation steps are taken from the scarb build script
# https://github.com/software-mansion/scarb/blob/main/install.sh
ENV SCARB_VERSION="v2.8.2"
ENV SCARB_REPO="https://github.com/software-mansion/scarb/releases/download"
ENV PLATFORM="x86_64-unknown-linux-gnu"
ENV SCARB_TARGET="/usr/src/scarb.tar.gz"

RUN curl -fLS -o $SCARB_TARGET \
    $SCARB_REPO/$SCARB_VERSION/scarb-$SCARB_VERSION-$PLATFORM.tar.gz && \
    tar -xz -C /usr/src/ --strip-components=1 -f $SCARB_TARGET && \
	mv /usr/src/bin/scarb /bin

# Set the compilation directory
WORKDIR /usr/src/madara

# Build the application in release mode
RUN cargo build --release

# Stage 2: Create the final runtime image
FROM debian:bookworm

# Install runtime dependencies
RUN apt-get -y update && \
    apt-get install -y openssl ca-certificates busybox && \
    apt-get autoremove -y; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /usr/local/bin

# Copy the compiled binary from the builder stage
COPY --from=builder /usr/src/madara/target/release/madara .

# Copies the runner. This is responsible for reading secrets and launching
# madara
COPY ./madara-runner.sh .
RUN chmod a+x ./madara-runner.sh

# Set the entrypoint
CMD ["/usr/local/bin/madara-runner.sh"]
