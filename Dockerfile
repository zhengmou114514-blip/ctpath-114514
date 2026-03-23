# 使用包含 CUDA 11.8 和 PyTorch 2.0 的官方镜像（兼容性好，且比 CUDA 12 镜像稍微小一点）
FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-devel

# 设置工作目录
WORKDIR /workspace

# 更换阿里源以加速安装（可选，视网络情况而定）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 复制当前目录下的所有文件到容器中
COPY . /workspace

# 安装依赖
# 注意：通常需要安装 torch-geometric 等图神经网络库，这里预留命令
RUN pip install -r requirements.txt || echo "No requirements.txt found, skipping..."

# 补充安装论文可能需要的常用库
RUN pip install scikit-learn pandas numpy matplotlib