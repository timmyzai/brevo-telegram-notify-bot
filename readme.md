*** Initial Configuration ***
brew install python@3.12.0
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

*** Zappa Deployment ***
- Make sure you have done AWS Configure and your IAM has the permission to proceed
zappa init (Just for the first time)
zappa deploy staging
zappa update staging


*** Other Commands ***
// quit from current env
deactivate

// remove old env
rm -rf /Users/myav/venvs/myenv 

// activate the virtual env
source venv/bin/activate

// make sure Zappa is in the correct env
which zappa  
zappa --version