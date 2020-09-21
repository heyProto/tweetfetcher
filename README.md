# Introduction
This program searches for tweets based on hashtags input by the user and saves them in tweet-data/tweet-data.db.

# Setup
Run
```shell
virtualenv ENV --python=python3
pip install -r requirements.txt 
```
in root of project folder. 

Then run
```shell
python tweet_fetcher.py
```

Enter the hashtags separated by a comma. Spaces before or after commas are allowed.

## Update changes to lambda
Copy file lambda_function.py to directory tweet-fetcher-lambda. Compress contents of the directory(not the directory itself but the contents of the directory) and push the zip to lambda.
