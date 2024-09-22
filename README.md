<!-- markdownlint-disable -->
<div align="center">
  <img src="https://github.com/madara-alliance/madara-bench/blob/main/res/banner.png" style="width: 100%; height: auto; object-fit: cover; object-position: center;">
</div>
<div align="center">
<br />
<!-- markdownlint-restore -->

</div>

> A simple [Starknet](https://www.starknet.io/) **RPC benchmarking tool**

## Table of content

- [How it works](#how-it-works)
- [Dependencies](#dependencies)
- [Running](#running)
- [Benchmarks](#benchmarks)

## How it works

**MADARA bench** runs various Starknet RPC nodes in isolated, resource-constrained
containers for testing. These nodes are automatically set up and 
have their RPC endpoints opened up for you to test using an online api 
(served with [FastAPI](https://github.com/fastapi/fastapi)).

## Dependencies

> [!TIP]
> If you are using [Nixos](https://nixos.org/) or the [nix](https://nixos.org/)
> package manager, you can skip to [running](#nix) (you will still need to
> [specify secrets](#step-4-specifying-secrets)).

**MADARA bench** currently only supports running on _linux_ and requires 
[docker](https://docs.docker.com/engine/install/) and 
[docker-compose](https://docs.docker.com/compose/install/) to be installed on
the host system.

#### Step 1: _installing build-essential_

This is needed by certain python packages

```bash
sudo apt update
sudo apt install build-essential
```

#### Step 2: _installing python 3.12_

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.12 python3.12-venv
```

#### Step 3: _installing poetry_ (python package manager)

> [_official instructions_](https://python-poetry.org/docs/#installing-with-the-official-installer)

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### Step 4: _specifying secrets_

The following are required for **MADARA bench** to start:

```bash
echo abc > secrets/gateway_key.secret
echo https://eth-sepolia.g.alchemy.com/abc > secrets/rpc_api.secret
echo wss://eth-sepolia.g.alchemy.com/abc > secrets/rpc_api_ws.secret
```

You can get an RPC api key frm [Alchemy](https://www.alchemy.com/),
[Infura](https://www.infura.io/) or [BlastAPI](https://blastapi.io/), amongst
others. `gateway_key` is a special key which has been given out to node 
development teams in the ecosystem and is used to bypass sequencer rate limits 
for testing purposes. _It is not available publicly_.

> [!IMPORTANT]
> By default, **MADARA bench** runs on _starknet testnet_, and you will need
> your RPC api keys to point to _ethereum sepolia_ for this to work.

## Running

To start **MADARA bench**, run the following command:

```bash
make start
```

This will automatically build docker images for each RPC node, create
individual volumes for each databases, start the nodes and serve a FastAPI
endpoint at [0.0.0.0:8000/docs](http://0.0.0.0:8000/docs).

> [!WARNING]
> If this is the first time you are running **MADARA bench**, sit back and grab
> a cup of coffee as building the node images can take a while.

To stop **MADARA bench**, run:

```bash
make stop
```

You can also get a list of all available commands by running:

```bash
make help
```

---

## Nix

If you are using [Nixos](https://nixos.org/) or the [nix](https://nixos.org/) 
package manager, you do not need to install any dependencies and can instead 
just run:

```bash
nix develop --extra-experimental-features "nix-command flakes" .#start
```

This will download every dependency into a [development shell](https://nixos.wiki/wiki/Development_environment_with_nix-shell), 
independent of the rest of your system and start **MADARA bench**. This is the 
_preferred way_ of running **MADARA bench** and will also handle auto-closing 
docker containers for you.

---

## As a service

> [!IMPORTANT]
> The following instructions assume you have set up **MADARA bench** to run
> under [nix](#nix).

You should make sure the user you are using to run **MADARA bench** as a
service is part of the `docker` group. This way you can run it as a _user 
service_ instead of a _root service_.

To run **MADARA bench** as a user service, follow these instructions:

1. Replace `/path/to/madara-bench` in `madara-bench.service` with its actual
path

2. If it does not exist already, create `$HOME/.config/systemd/user/`:
```bash
mkdir -p $HOME/.config/systemd/user
```

3. Copy over `madara-bench.service` to `$HOME/.config/systemd/user/`:
```bash
cp madara-bench.service $HOME/.config/systemd/user
```

4. Start the service:
```bash
systemctl --user daemon-reload
systemctl --user enable madara-bench.service
systemctl --user start madara-bench.service
journalctl --user -u madara-bench -f
```

## Benchmarks

Once you have started **MADARA bench**, start by heading to your 
[FastAPI endpoint](http://0.0.0.0:8000/docs). There you will see multiple
sections:

- `bench`: run system and RPC benchmarks
- `system`: display system metrics (CPU, memory and storage usage)
- `read`: query individual RPC methods on each node
- `trace`: run tracing RPC calls on each node
- `debug`: display useful extra information

RPC benchmarks are _procedural_, that is to say inputs are generated 
automatically as the chain keeps making progress. This way, you do not need to
worry about passing valid or up-to-date parameters, you can just focus on
benchmarking.

> [!NOTE]
> When needed, RPC method inputs are generated by sampling from a random point 
> in the last 1000 blocks of the chain. For a more concrete example of how this
>  works, check [`generators.py`](https://github.com/madara-alliance/madara-bench/blob/main/app/benchmarks/generators.py).

Currently, only a few RPC methods are supported for benchmarking, with more to
be added in the future. You can request coverage of new RPC methods in an
[issue](https://github.com/madara-alliance/madara-bench/issues).
