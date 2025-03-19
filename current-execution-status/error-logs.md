
{
  "insertId": "67da1935000dea14e3a00230",
  "httpRequest": {
    "requestMethod": "GET",
    "requestUrl": "https://palios-taey-yb6xskdufa-uc.a.run.app/",
    "requestSize": "556",
    "status": 500,
    "responseSize": "204",
    "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Safari/605.1.15",
    "remoteIp": "73.56.93.57",
    "serverIp": "216.239.38.53",
    "latency": "0.783137066s",
    "protocol": "HTTP/1.1"
  },
  "resource": {
    "type": "cloud_run_revision",
    "labels": {
      "revision_name": "palios-taey-00007-2gd",
      "configuration_name": "palios-taey",
      "service_name": "palios-taey",
      "project_id": "palios-taey-dev",
      "location": "us-central1"
    }
  },
  "timestamp": "2025-03-19T01:09:09.120515Z",
  "severity": "ERROR",
  "labels": {
    "instanceId": "00fd7d7337b92c1da71fe09ccd2143d75952908342dd2152efa0c5ea25dbe4a7fe856896c4741295e5b3d97deb744d609ae76ba248a41a3009bf485b077e1c16260928b1"
  },
  "logName": "projects/palios-taey-dev/logs/run.googleapis.com%2Frequests",
  "trace": "projects/palios-taey-dev/traces/7e8990a946474907823bf1ee8ebc6848",
  "receiveTimestamp": "2025-03-19T01:09:09.920493417Z",
  "spanId": "56365c94a21f5f45",
  "traceSampled": true
}

{
  "textPayload": "Traceback (most recent call last):\n  File \"/usr/local/lib/python3.10/site-packages/gunicorn/workers/gthread.py\", line 281, in handle\n    keepalive = self.handle_request(req, conn)\n  File \"/usr/local/lib/python3.10/site-packages/gunicorn/workers/gthread.py\", line 333, in handle_request\n    respiter = self.wsgi(environ, resp.start_response)\nTypeError: FastAPI.__call__() missing 1 required positional argument: 'send'",
  "insertId": "67da1935000de59fc72b49db",
  "resource": {
    "type": "cloud_run_revision",
    "labels": {
      "configuration_name": "palios-taey",
      "location": "us-central1",
      "service_name": "palios-taey",
      "project_id": "palios-taey-dev",
      "revision_name": "palios-taey-00007-2gd"
    }
  },
  "timestamp": "2025-03-19T01:09:09.910751Z",
  "severity": "ERROR",
  "labels": {
    "instanceId": "00fd7d7337b92c1da71fe09ccd2143d75952908342dd2152efa0c5ea25dbe4a7fe856896c4741295e5b3d97deb744d609ae76ba248a41a3009bf485b077e1c16260928b1"
  },
  "logName": "projects/palios-taey-dev/logs/run.googleapis.com%2Fstderr",
  "receiveTimestamp": "2025-03-19T01:09:10.241351152Z",
  "errorGroups": [
    {
      "id": "CN2RiP3Jo5_slAE"
    }
  ]
}

{
  "insertId": "67da1940000e6b6d997b8fa9",
  "httpRequest": {
    "requestMethod": "GET",
    "requestUrl": "https://palios-taey-yb6xskdufa-uc.a.run.app/health",
    "requestSize": "537",
    "status": 500,
    "responseSize": "204",
    "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Safari/605.1.15",
    "remoteIp": "73.56.93.57",
    "serverIp": "216.239.38.53",
    "latency": "0.002684711s",
    "protocol": "HTTP/1.1"
  },
  "resource": {
    "type": "cloud_run_revision",
    "labels": {
      "revision_name": "palios-taey-00007-2gd",
      "service_name": "palios-taey",
      "project_id": "palios-taey-dev",
      "location": "us-central1",
      "configuration_name": "palios-taey"
    }
  },
  "timestamp": "2025-03-19T01:09:20.939445Z",
  "severity": "ERROR",
  "labels": {
    "instanceId": "00fd7d7337b92c1da71fe09ccd2143d75952908342dd2152efa0c5ea25dbe4a7fe856896c4741295e5b3d97deb744d609ae76ba248a41a3009bf485b077e1c16260928b1"
  },
  "logName": "projects/palios-taey-dev/logs/run.googleapis.com%2Frequests",
  "trace": "projects/palios-taey-dev/traces/9dce0bf3944c2bd31feb981e6b4adb8d",
  "receiveTimestamp": "2025-03-19T01:09:20.951643490Z",
  "spanId": "f47262cfab02b667",
  "traceSampled": true
}
{
  "textPayload": "Traceback (most recent call last):\n  File \"/usr/local/lib/python3.10/site-packages/gunicorn/workers/gthread.py\", line 281, in handle\n    keepalive = self.handle_request(req, conn)\n  File \"/usr/local/lib/python3.10/site-packages/gunicorn/workers/gthread.py\", line 333, in handle_request\n    respiter = self.wsgi(environ, resp.start_response)\nTypeError: FastAPI.__call__() missing 1 required positional argument: 'send'",
  "insertId": "67da1940000e68d1cb35fc73",
  "resource": {
    "type": "cloud_run_revision",
    "labels": {
      "revision_name": "palios-taey-00007-2gd",
      "service_name": "palios-taey",
      "project_id": "palios-taey-dev",
      "location": "us-central1",
      "configuration_name": "palios-taey"
    }
  },
  "timestamp": "2025-03-19T01:09:20.944337Z",
  "severity": "ERROR",
  "labels": {
    "instanceId": "00fd7d7337b92c1da71fe09ccd2143d75952908342dd2152efa0c5ea25dbe4a7fe856896c4741295e5b3d97deb744d609ae76ba248a41a3009bf485b077e1c16260928b1"
  },
  "logName": "projects/palios-taey-dev/logs/run.googleapis.com%2Fstderr",
  "receiveTimestamp": "2025-03-19T01:09:20.951360395Z",
  "errorGroups": [
    {
      "id": "CN2RiP3Jo5_slAE"
    }
  ]
}
{
  "insertId": "67da19490007ecf5fb5cea5c",
  "httpRequest": {
    "requestMethod": "GET",
    "requestUrl": "https://palios-taey-yb6xskdufa-uc.a.run.app/health",
    "requestSize": "537",
    "status": 500,
    "responseSize": "204",
    "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Safari/605.1.15",
    "remoteIp": "73.56.93.57",
    "serverIp": "216.239.38.53",
    "latency": "0.003634941s",
    "protocol": "HTTP/1.1"
  },
  "resource": {
    "type": "cloud_run_revision",
    "labels": {
      "location": "us-central1",
      "service_name": "palios-taey",
      "configuration_name": "palios-taey",
      "revision_name": "palios-taey-00007-2gd",
      "project_id": "palios-taey-dev"
    }
  },
  "timestamp": "2025-03-19T01:09:29.512347Z",
  "severity": "ERROR",
  "labels": {
    "instanceId": "00fd7d7337b92c1da71fe09ccd2143d75952908342dd2152efa0c5ea25dbe4a7fe856896c4741295e5b3d97deb744d609ae76ba248a41a3009bf485b077e1c16260928b1"
  },
  "logName": "projects/palios-taey-dev/logs/run.googleapis.com%2Frequests",
  "trace": "projects/palios-taey-dev/traces/553b765e6cff583c268db8719570a721",
  "receiveTimestamp": "2025-03-19T01:09:29.608915094Z",
  "spanId": "42cf10ff61c4b139"
}
{
  "textPayload": "Traceback (most recent call last):\n  File \"/usr/local/lib/python3.10/site-packages/gunicorn/workers/gthread.py\", line 281, in handle\n    keepalive = self.handle_request(req, conn)\n  File \"/usr/local/lib/python3.10/site-packages/gunicorn/workers/gthread.py\", line 333, in handle_request\n    respiter = self.wsgi(environ, resp.start_response)\nTypeError: FastAPI.__call__() missing 1 required positional argument: 'send'",
  "insertId": "67da19490007e6e4ee963de5",
  "resource": {
    "type": "cloud_run_revision",
    "labels": {
      "location": "us-central1",
      "revision_name": "palios-taey-00007-2gd",
      "configuration_name": "palios-taey",
      "service_name": "palios-taey",
      "project_id": "palios-taey-dev"
    }
  },
  "timestamp": "2025-03-19T01:09:29.517860Z",
  "severity": "ERROR",
  "labels": {
    "instanceId": "00fd7d7337b92c1da71fe09ccd2143d75952908342dd2152efa0c5ea25dbe4a7fe856896c4741295e5b3d97deb744d609ae76ba248a41a3009bf485b077e1c16260928b1"
  },
  "logName": "projects/palios-taey-dev/logs/run.googleapis.com%2Fstderr",
  "receiveTimestamp": "2025-03-19T01:09:29.610515847Z",
  "errorGroups": [
    {
      "id": "CN2RiP3Jo5_slAE"
    }
  ]
}






