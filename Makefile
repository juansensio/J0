PORT = $(shell uv run mpremote connect list | awk '/303a:4001/ {print $$1; exit}')
DEVICE := id:123456

flash-id:
	uv run esptool flash-id

erase-flash:
	uv run esptool erase_flash

write-flash:
	uv run esptool --baud 460800 write_flash 0 ESP32_GENERIC_S3-20260824-v1.29.0.bin

list:
	uv run mpremote connect list

repl:
# 	@echo "Connecting to $(PORT)"
# 	uv run mpremote connect $(PORT) repl
# 	uv run mpremote connect $(DEVICE) repl
	uv run mpremote repl

run:
	uv run mpremote run $(or $(word 2,$(MAKECMDGOALS)),main.py)

dev:
	uv run mpremote mount . run main.py

deploy:
	@test -f wifi_config.py || (echo "Copy wifi_config.example.py to wifi_config.py first"; exit 1)
	uv run mpremote cp -r src :
	uv run mpremote cp boot.py :boot.py
	uv run mpremote cp wifi_config.py :wifi_config.py
	uv run mpremote cp main.py :main.py
	uv run mpremote reset

ROBOT_HOST ?=
ROBOT_TOKEN ?=

status demo forward backward stop reset:
	@test -n "$(ROBOT_HOST)" || (echo "Set ROBOT_HOST to the IP printed by the robot"; exit 1)
	@test -n "$(ROBOT_TOKEN)" || (echo "Set ROBOT_TOKEN to CONTROL_TOKEN from wifi_config.py"; exit 1)
	curl --fail --show-error --max-time 5 -H "X-Robot-Token: $(ROBOT_TOKEN)" "http://$(ROBOT_HOST)/$(if $(filter status,$@),,$@)"

cp:
	uv run mpremote cp $(or $(word 2,$(MAKECMDGOALS)),main.py) :$(or $(word 2,$(MAKECMDGOALS)),main.py)

ls:
	uv run mpremote ls

mkdir:
	uv run mpremote mkdir $(or $(word 2,$(MAKECMDGOALS)),src)

rm:
	uv run mpremote rm $(or $(word 2,$(MAKECMDGOALS)),$(or $(word 2,$(MAKECMDGOALS)),main.py))

%.py:
	@:

gif:
	bash scripts/prepare-video.sh $(or $(word 2,$(MAKECMDGOALS)),*.MOV)

test:
	env -u VIRTUAL_ENV uv run python -m pytest tests/
