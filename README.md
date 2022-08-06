# prometheus-http-sd

This is a
[Prometheus HTTP SD](https://prometheus.io/docs/prometheus/latest/http_sd/)
framework.

[![Test](https://github.com/laixintao/prometheus-http-sd/actions/workflows/test.yaml/badge.svg)](https://github.com/laixintao/prometheus-http-sd/actions/workflows/test.yaml)

<!-- vim-markdown-toc GFM -->

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Admin Page](#admin-page)
  - [Serve under a different root path](#serve-under-a-different-root-path)
- [Define you targets](#define-you-targets)
  - [Check and Validate your Targets](#check-and-validate-your-targets)
  - [Script Dependencies](#script-dependencies)
- [The Target Path](#the-target-path)
- [Update Your Scripts](#update-your-scripts)
- [Best Practice](#best-practice)

<!-- vim-markdown-toc -->

## Features

- Support static targets from Json file;
- Support static targets from Yaml file;
- Support generating target list using Python script;
- Support `check` command, to testing the generated target is as expected, and
  counting the targets.

## Installation

```shell
pip install prometheus-http-sd
```

## Usage

First, you need a directory, everything in this directory will be used to
generate targets for prometheus-http-sd.

```shell
$ mkdir targets
```

In this directory:

- Filename that ending with `.json` will be exposed directly
- Filename that ending with `.yaml` will be exposed directly
- Filename that ending with `.py` must include a `generate_targets()` function,
  the function will be run, and it must return a `TargetList` (Type helper in
  `prometheus_http_sd.targets.`)
- Filename that starts with `_` will be ignored, so you can have some python
  utils there, for e.g. `_utils/__init__.py` that you can import in you
  `generate_targets()`
- Filename that starts with `.` (hidden file in Linux) will also be ignored

Then you can run `prometheus-http-sd serve -h 0.0.0.0 -p 8080 /tmp/targets`,
prometheus-http-sd will start to expose targets at: http://0.0.0.0:8080/targets

The `-h` and `-p` is optional, defaults to `127.0.0.1` and `8080`.

```shell
$ prometheus-http-sd /tmp/good_root
[2022-07-24 00:52:03,896] {wasyncore.py:486} INFO - Serving on http://127.0.0.1:8080
```

### Admin Page

You can open the root path, `http://127.0.0.1:8080/` in this example, and you
will see all of the available paths list in the admin page.

![](./docs/admin.png)

### Serve under a different root path

If you put prometheus-http-sd behind a reverse proxy like Nginx, like this:

```
location /http_sd/ {
      proxy_pass http://prometheus_http_sd;
}
```

Then you need to tell prometheus_http_sd to serve all HTTP requests under this
path, by using the `--url_prefix /http_sd` cli option, (or `-r /http_sd` for
short).

## Define you targets

### Check and Validate your Targets

You can use `prometheus-http-sd check` command to test your targets dir. It will
run all of you generators, validate the targets, and print the targets count
that each generator generates.

```shell
$ prometheus-http-sd check test/test_generator/root
[2022-08-06 00:50:11,095] {validate.py:16} INFO - Run generator test/test_generator/root/json/target.json, took 0.0011398792266845703s, generated 1 targets.
[2022-08-06 00:50:11,100] {validate.py:16} INFO - Run generator test/test_generator/root/yaml/target.yaml, took 0.0043718814849853516s, generated 2 targets.
[2022-08-06 00:50:11,100] {validate.py:22} INFO - Done! Generated {total_targets} in total.
```

It's a good idea to use `prometheus-http-sd check` in your CI system to validate
your targets generator scripts and target files.

### Script Dependencies

If you want your scripts to use some other python library, just install them
into the **same virtualenv** that you install prometheus-http-sd, so that
prometheus-http-sd can import them.

## The Target Path

prometheus-http-sd support sub-pathes.

For example, if we use `prometheus-http-sd serve gateway`, and the `gateway`
directory's structure is as follows:

```shell
gateway
├── nginx
│   ├── edge.py
│   └── targets.json
└── targets.json
```

Then:

- `/targets/gateway` will return the targets from:
  - `gateway/nginx/edge.py`
  - `gateway/nginx/targets.json`
  - `gateway/targets.json`
- `/targets/gateway/nginx` will return the targets from:
  - `gateway/nginx/edge.py`
  - `gateway/nginx/targets.json`

This is very useful when you use vertical scaling. Say you have 5 Prometheus
instances, and you want each one of them scrape for different targets, then you
can use the sub-path feature of prometheus-http-sd.

For example, in one Prometheus's scrape config:

```yaml
scrape_configs:
  - job_name: "nginx"
    http_sd_config:
      url: http://prometheus-http-sd:8080/targets/nginx

  - job_name: "etcd"
    http_sd_config:
      url: http://prometheus-http-sd:8080/targets/etcd
```

And in another one:

```yaml
scrape_configs:
  - job_name: "nginx"
    http_sd_config:
      url: http://prometheus-http-sd:8080/targets/database

  - job_name: "etcd"
    http_sd_config:
      url: http://prometheus-http-sd:8080/targets/application
```

## Update Your Scripts

If you want to update your script file or target json file, just upload and
overwrite with your new version, it will take effect immediately after you
making changes, **there is no need to restart** prometheus-http-sd,
prometheus-http-sd will read the file (or reload the python script) every time
serving a request.

It is worth noting that restarting is safe because if Prometheus failed to get
the target list via HTTP request, it won't update its current target list to
empty, instead,
[it will keep using the current list](https://prometheus.io/docs/prometheus/latest/http_sd/).

> Prometheus caches target lists. If an error occurs while fetching an updated
> targets list, Prometheus keeps using the current targets list.

For the same reason, if there are 3 scripts under `/targets/mysystem` and only
one failed for a request, prometheus-http-sd will return a HTTP 500 Error for
the whole request instead of returning the partial targets from the other two
scripts.

Also for the same reason, if your script met any error, you should throw out
`Exception` all the way to the top instead of catch it in your script and return
a null `TargetList`, if you return a null `TargetList`, prometheus-http-sd will
think that your script run successfully and empty the target list as well.

You can notice this error from stdout logs or `/metrics` from
prometheus-http-sd.

## Best Practice

You can use a git repository to manage your target generator.
