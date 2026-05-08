#!/usr/bin/env python3
import json, re, sys, pathlib
text=pathlib.Path(sys.argv[1]).read_text(errors='replace')
nums=[]
for line in text.splitlines():
    if re.search(r'(HW|hardware).*latency|latency', line, re.I):
        nums += [float(x) for x in re.findall(r'(?<![A-Za-z])\d+(?:\.\d+)?(?=\s*(?:ms|msec|milliseconds)?)', line)]
out={"source": sys.argv[1], "raw_latency_numbers": nums}
if nums:
    out["hw_latency_ms"] = nums[-1]
    out["processing_fps_from_hw_latency"] = 1000.0 / nums[-1] if nums[-1] else None
print(json.dumps(out, indent=2))
