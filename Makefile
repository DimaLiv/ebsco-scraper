target=override

override container-name-app = ansible
override docker-compose = docker-compose -f docker-compose.yml -f docker-compose.$(target).yml

init: build run

# Docker

ps: FORCE ; $(docker-compose) ps
images: FORCE ; $(docker-compose) images
build: FORCE ; $(docker-compose) build --pull --progress=plain
up: FORCE ; $(docker-compose) up -d --remove-orphans --no-build
down: FORCE ; $(docker-compose) down --remove-orphans
push: FORCE ; $(docker-compose) push
pull: FORCE ; $(docker-compose) pull
logs: FORCE ; $(docker-compose) logs -f
exec: FORCE ; $(docker-compose) exec $(c) sh
remove-all: FORCE ; $(docker-compose) rm -f -s -v

run: FORCE ; $(docker-compose) up

# Hack

FORCE:
