# Testing system

## Building project

```shell
git clone https://github.com/PluxCo/testing_platform
cd testing_platform
```

```shell
sudo docker volume create testing-data
sudo docker build -t testing_platform .
sudo docker run -d \
  -e "TGTOKEN=<TELEGRAM_TOKEN>" \
  -e "ADMIN_PASSWD=<WEB_PASSWORD>" \
  --name testing  \
  -p 80:5000 \
  -v testing-data:/app/data \
  testing_platform
```