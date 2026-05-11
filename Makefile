.PHONY: sync-files sync-results run-detector-benchmark measure-latency prepare

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

HOST_IP ?= 10.10.10.21
HOST_USER ?= pi
HOST_PASSWORD ?=

ifeq ($(HOST_PASSWORD),)
	SSH_CMD = ssh $(HOST_USER)@$(HOST_IP)
	RSYNC_CMD = rsync -avz
else
	SSH_CMD = sshpass -p '$(HOST_PASSWORD)' ssh $(HOST_USER)@$(HOST_IP)
	RSYNC_CMD = sshpass -p '$(HOST_PASSWORD)' rsync -avz -e ssh
endif

sync-files:
	$(RSYNC_CMD) --delete \
		--exclude 'models/' \
		--exclude 'results/' \
		--exclude 'logs/' \
		--exclude 'dataset/' \
		--exclude '.env' \
		. $(HOST_USER)@$(HOST_IP):~/traffic-violation-detection-edge/

sync-results:
	$(RSYNC_CMD) $(HOST_USER)@$(HOST_IP):~/traffic-violation-detection-edge/results/ results/
	$(RSYNC_CMD) $(HOST_USER)@$(HOST_IP):~/traffic-violation-detection-edge/logs/ logs/

run-detector-benchmark:
	$(SSH_CMD) "cd ~/traffic-violation-detection-edge && ./detector-benchmark/scripts/00_check_environment.sh && ./detector-benchmark/scripts/run_all.sh"

measure-latency:
	@if [ -z "$(MODEL_PATH)" ]; then echo "Error: MODEL_PATH is required. Usage: make measure-latency MODEL_PATH=/path/to/model.hef"; exit 1; fi
	$(SSH_CMD) "hailortcli run --measure-latency $(MODEL_PATH)"

prepare: sync-files
	$(SSH_CMD) "cd ~/traffic-violation-detection-edge && ./setup/download_coco_val2017.sh"
	$(SSH_CMD) "cd ~/traffic-violation-detection-edge && python3 ./setup/download_video_footage_dataset.py"
	$(SSH_CMD) "cd ~/traffic-violation-detection-edge && python3 ./setup/download_models.py"
