# meta_fit

## Clone repo
```
git clone git@bitbucket.org:suzukiy/meta_fit.git
```

## Download test data and weights and put it to repo:
https://drive.google.com/drive/folders/17Q3TsWovNJWrC7VR389AvHVG5Mpve6sn?usp=share_link

## Build docker image:
```
make build
```

## Run docker container:
```
make run
```

## Run inference
```
python3 test.py --config configs/test_config.yaml
```
