from modelscope import snapshot_download

# 下载 BAAI 的 bge-reranker-base 模型到当前目录下的 "local_models" 文件夹
model_dir = snapshot_download('BAAI/bge-reranker-base', cache_dir='./local_models')
print(f"模型已下载到: {model_dir}")