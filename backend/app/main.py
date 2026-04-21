from fastapi import FastAPI

app = FastAPI(title='Sistema Gestión Aires UCC - Backend')

@app.get('/')
def read_root():
    return {'status': 'Running', 'module': 'Backend, Data Analysis, DB'}
