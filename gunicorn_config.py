workers = 4
bind = "0.0.0.0:10000"
timeout = 120
worker_class = "sync"
max_requests = 1000
max_requests_jitter = 50
keepalive = 5 