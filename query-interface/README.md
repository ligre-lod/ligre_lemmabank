# query-interface

LiGre Query Interface - A tool for querying the LiGre Lemma Bank.

You can use the tool right now at: https://ligre-lod.github.io/query-interface/

If you wish to run this tool on your machine you can simply install [Docker](https://www.docker.com/) and start the pre-built images with `docker compose up`. Otherwise, please refer to the development section below.

# Development

## Project Structure

This tool is composed of the following components:

- `apps/frontend/` - React frontend application

## Requirements

It is recommended to use [nix](https://nix.dev/) and [direnv](https://direnv.net/) and let them take care of requirements.

Otherwise, you will need to install the requirements listed in each component's documentation.

## Getting started

If you're using `nix` you can simply run `mprocs` and a local development environment will be running in a few moments.

Otherwise, you will need to start each component yourself as described in their respective documentation.

