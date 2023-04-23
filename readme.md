
### install the requirements
```
pip install --no-cache-dir --upgrade -r requirements.txt
```

### start the executor
```
celery -A bot-main worker -l info --pool=solo 
``` 
#### start mock server
```
uvicorn server:app --host 0.0.0.0 --reload
```


other commands
```
#### celery.exe -A bot-main worker -l info -c 1
#### celery.exe flower --address=127.0.0.1 --port=5566
#### pipreqs . --encoding UTF-8 --use-local
```

https://beautifulsoup.readthedocs.io/zh_CN/v4.4.0/
