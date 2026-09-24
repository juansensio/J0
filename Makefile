PORT := $(shell uv run mpremote connect list | awk '/303a:4001/ {print $$1; exit}')
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
	uv run mpremote cp -r src :
	uv run mpremote cp boot.py :boot.py
	uv run mpremote cp main.py :main.py
	uv run mpremote reset

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