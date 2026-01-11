## 环境准备

### 依赖


```python
# conda env list
```


```python
# !pip install "pymilvus[model]==2.5.10" openai==1.82.0 requests==2.32.3 tqdm==4.67.1 torch==2.7.0 ipywidgets
```


```python
import os

api_key = os.getenv("DEEPSEEK_API_KEY")
```

### 准备数据

数据准备执行一次就可以，下面注释


```python
#!wget https://github.com/milvus-io/milvus-docs/releases/download/v2.4.6-preview/milvus_docs_2.4.x_en.zip
```


```python
#!unzip -q milvus_docs_2.4.x_en.zip -d milvus_docs
```

先拼接全部 markdown，再以 markdown 标题末尾分割


```python
# 分割总段落数
len(text_lines)
```




    72




```python
from glob import glob

text_lines = []

for file_path in glob("milvus_docs/en/faq/*.md", recursive=True):
    with open(file_path, "r") as file:
        file_text = file.read()
    text_lines += file_text.split("# ")
```

### 准备 LLM 和 Embedding 模型


```python
from openai import OpenAI

deepseek_client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com/v1"
)
```

定义 embedding 模型，使用 `milvus_model` 来生成文本嵌入。以 `DefaultEmbeddingFunction` 模型为例，这是一个预训练的轻量级嵌入模型。


```python
from pymilvus import model as milvus_model

# embedding_model = milvus_model.dense.OpenAIEmbeddingFunction(
#     model_name='text-embedding-3-large', # Specify the model name
#     api_key='sk-XXX', # Provide your OpenAI API key
#     base_url='https://api.apiyi.com/v1',
#     dimensions=512
# )

embedding_model = milvus_model.DefaultEmbeddingFunction()
```

生成一个测试嵌入并打印其维度和前几个元素。


```python
test_embedding = embedding_model.encode_queries(["how are you"])[0]
embedding_dim = len(test_embedding)
print(embedding_dim)
print(test_embedding[:10])
```

    768
    [-0.04836059  0.07163021 -0.01130063 -0.03789341 -0.03320651 -0.01318453
     -0.03041721 -0.02269495 -0.02317858 -0.00426026]



```python
test_embedding_0 = embedding_model.encode_queries(["How are you"])[0]
print(test_embedding_0[:10])
```

    [-0.0006078   0.01157839  0.07231993 -0.04240938 -0.01230968  0.00448868
      0.05736424 -0.03771587 -0.00926352 -0.00540186]


可以发现这两句话是有区别的

## 加载数据至Milvus

### 创建 Collection


```python
from pymilvus import MilvusClient
# 消除警告
import warnings
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

milvus_client = MilvusClient(uri="./milvus_demo.db")

collection_name = "my_rag_collection"
```

demo 测试，如果存在collection，先删除


```python
# demo 测试，如果存在collection，先删除
if milvus_client.has_collection(collection_name):
    milvus_client.drop_collection(collection_name)
```

创建集合


```python
milvus_client.create_collection(
    collection_name=collection_name,
    dimension=embedding_dim, # 向量维度
    metric_type="IP",  # 内积距离
    consistency_level="Strong",  # 支持的值为 (`"Strong"`, `"Session"`, `"Bounded"`, `"Eventually"`)。更多详情请参见 https://milvus.io/docs/consistency.md#Consistency-Level。
)
```

如果不指定任何字段信息，Milvus 将自动创建一个默认的 `id` 字段作为主键，以及一个 `vector` 字段来存储向量数据。一个保留的 JSON 字段用于存储非 schema 定义的字段及其值。

- `metric_type` (距离度量类型):
    - 作用：定义如何计算向量之间的相似程度。
    - 例如：`IP` (内积) - 值越大通常越相似；`L2` (欧氏距离) - 值越小越相似；`COSINE` (余弦相似度) - 通常转换为距离，值越小越相似。
    - 选择依据：根据你的嵌入模型的特性和期望的相似性定义来选择。

- `consistency_level` (一致性级别):
    - 作用：定义数据写入后，读取操作能多快看到这些新数据。
    - 例如：
        - `Strong` (强一致性): 总是读到最新数据，可能稍慢。
        - `Bounded` (有界过期): 可能读到几秒内旧数据，性能较好 (默认)。
        - `Session` (会话一致性): 自己写入的自己能立刻读到。
        - `Eventually` (最终一致性): 最终会读到新数据，但没时间保证，性能最好。
     选择依据：在数据实时性要求和系统性能之间做权衡。

简单来说：
- `metric_type`：怎么算相似。
- `consistency_level`：新数据多久能被读到。

### 插入数据


```python
from tqdm import tqdm # 进度条用法

data = []
# 将所有的段落进行向量化 [[-0.00364136, -0.0018697,...], [-2.94084388e-02,  8.61209233e-02...], ...]
doc_embeddings = embedding_model.encode_documents(text_lines)
# print(doc_embeddings[:10])
for i, line in enumerate(tqdm(text_lines, desc="Creating embeddings")):
    data.append({"id": i, "vector": doc_embeddings[i], "text": line})

milvus_client.insert(collection_name=collection_name, data=data)
```

    Creating embeddings: 100%|██████████| 72/72 [00:00<00:00, 605190.16it/s]





    {'insert_count': 72, 'ids': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71], 'cost': 0}



tqdm 进度条用法：


```python
# from tqdm import tqdm
# import time
# for i in tqdm(range(100), desc="倒计时"):
#     time.sleep(0.01)
```

    倒计时: 100%|██████████| 100/100 [00:01<00:00, 97.47it/s]


## 构建 RAG

### 检索查询数据

指定一个问题


```python
question = "what is milvus?"

search_res = milvus_client.search(
    collection_name=collection_name,
    data=embedding_model.encode_queries(
        [question]
    ),  # 将问题转换为嵌入向量
    limit=3,  # 返回前3个结果
    search_params={"metric_type": "IP", "params": {}},  # 内积距离
    output_fields=["text"],  # 返回 text 字段
)
```

输出结果


```python
# print(search_res)
search_res[0][0]
```




    {'id': 31, 'distance': 0.5377484560012817, 'entity': {'text': 'How does Milvus handle vector data types and precision?\n\nMilvus supports Binary, Float32, Float16, and BFloat16 vector types.\n\n- Binary vectors: Store binary data as sequences of 0s and 1s, used in image processing and information retrieval.\n- Float32 vectors: Default storage with a precision of about 7 decimal digits. Even Float64 values are stored with Float32 precision, leading to potential precision loss upon retrieval.\n- Float16 and BFloat16 vectors: Offer reduced precision and memory usage. Float16 is suitable for applications with limited bandwidth and storage, while BFloat16 balances range and efficiency, commonly used in deep learning to reduce computational requirements without significantly impacting accuracy.\n\n###'}}



补充：列表推导式


```python
# ## 从列表生成字典
# words = ["apple", "banana", "pear"]
# dict1 = {word: len(word) for word in words}
# print(dict1) # {'apple': 5, 'banana': 6, 'pear': 4}

# ## 带条件的推导式
# dict2 = {word: len(word) for word in words if len(word) > 5}
# print(dict2) # {'banana': 6}

# ## 从2个数组创建字典
# keys = ["a", "b", "c"]
# values = [1, 2, 3]
# dict3 = {k: v for k, v in zip(keys, values)}
# print(dict3) # {'a': 1, 'b': 2, 'c': 3}

# ## 转换现有字典
# o_dict = {"a": 1, "b": 2, "c": 3}
# n_dict = {k: v for k, v in o_dict.items() if v > 1}
# print(n_dict) # {'b': 2, 'c': 3}

# ## 与for循环的对比
# squares = {k: k**2 for k in range(1, 6)}
# print(squares) # {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}
# squares2 = {}
# for x in range(1, 6):
#     squares2[x] = x**2
# print(squares2) # {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}

```

    {'apple': 5, 'banana': 6, 'pear': 4}
    {'banana': 6}
    {'a': 1, 'b': 2, 'c': 3}
    {'b': 2, 'c': 3}
    {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}
    {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}


提取文本、相似度，并格式化


```python
retrieved_lines_with_distances = [
    (res["entity"]["text"], res["distance"]) for res in search_res[0]
]
print(json.dumps(retrieved_lines_with_distances))
```

    [["How does Milvus handle vector data types and precision?\n\nMilvus supports Binary, Float32, Float16, and BFloat16 vector types.\n\n- Binary vectors: Store binary data as sequences of 0s and 1s, used in image processing and information retrieval.\n- Float32 vectors: Default storage with a precision of about 7 decimal digits. Even Float64 values are stored with Float32 precision, leading to potential precision loss upon retrieval.\n- Float16 and BFloat16 vectors: Offer reduced precision and memory usage. Float16 is suitable for applications with limited bandwidth and storage, while BFloat16 balances range and efficiency, commonly used in deep learning to reduce computational requirements without significantly impacting accuracy.\n\n###", 0.5377484560012817], ["What data types does Milvus support on the primary key field?\n\nIn current release, Milvus supports both INT64 and string.\n\n###", 0.5187207460403442], ["Does Milvus support message engines other than Pulsar?\n\nYes. Kafka is supported in Milvus 2.1.0.\n\n###", 0.510108232498169]]


### 使用LLM获取RAG响应


```python
# 拼接查询到的上下文
context = "".join(
    [
        line_with_distance[0] for line_with_distance in retrieved_lines_with_distances
    ])
```

输出一下


```python
# 输出一下
context
```




    'How does Milvus handle vector data types and precision?\n\nMilvus supports Binary, Float32, Float16, and BFloat16 vector types.\n\n- Binary vectors: Store binary data as sequences of 0s and 1s, used in image processing and information retrieval.\n- Float32 vectors: Default storage with a precision of about 7 decimal digits. Even Float64 values are stored with Float32 precision, leading to potential precision loss upon retrieval.\n- Float16 and BFloat16 vectors: Offer reduced precision and memory usage. Float16 is suitable for applications with limited bandwidth and storage, while BFloat16 balances range and efficiency, commonly used in deep learning to reduce computational requirements without significantly impacting accuracy.\n\n###What data types does Milvus support on the primary key field?\n\nIn current release, Milvus supports both INT64 and string.\n\n###Does Milvus support message engines other than Pulsar?\n\nYes. Kafka is supported in Milvus 2.1.0.\n\n###'



打印一下在上方提出的问题


```python
# 问题
question
```




    'what is milvus?'



组装PROMPT


```python
SYSTEM_PROMPT = """
Human: 你是一个 AI 助手。你能够从提供的上下文段落片段中找到问题的答案。
"""

USER_PROMPT = f"""
请使用以下用 <context> 标签括起来的信息片段来回答用 <question> 标签括起来的问题。最后追加原始回答的中文翻译，并用 <translated>和</translated> 标签标注。
<context>
{context}
</context>
<question>
{question}
</question>
<translated>
</translated>
"""
```

输出一下PROMPT


```python
USER_PROMPT
```




    '\n请使用以下用 <context> 标签括起来的信息片段来回答用 <question> 标签括起来的问题。最后追加原始回答的中文翻译，并用 <translated>和</translated> 标签标注。\n<context>\nHow does Milvus handle vector data types and precision?\n\nMilvus supports Binary, Float32, Float16, and BFloat16 vector types.\n\n- Binary vectors: Store binary data as sequences of 0s and 1s, used in image processing and information retrieval.\n- Float32 vectors: Default storage with a precision of about 7 decimal digits. Even Float64 values are stored with Float32 precision, leading to potential precision loss upon retrieval.\n- Float16 and BFloat16 vectors: Offer reduced precision and memory usage. Float16 is suitable for applications with limited bandwidth and storage, while BFloat16 balances range and efficiency, commonly used in deep learning to reduce computational requirements without significantly impacting accuracy.\n\n###What data types does Milvus support on the primary key field?\n\nIn current release, Milvus supports both INT64 and string.\n\n###Does Milvus support message engines other than Pulsar?\n\nYes. Kafka is supported in Milvus 2.1.0.\n\n###\n</context>\n<question>\nwhat is milvus?\n</question>\n<translated>\n</translated>\n'



使用 DeepSeek 提供的 `deepseek-chat` 模型根据提示生成响应。


```python
response = deepseek_client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT},
    ],
)
print(response.choices[0].message.content)
```

    Based on the provided context, Milvus is a system that handles vector data types (such as Binary, Float32, Float16, and BFloat16) and supports primary key fields with INT64 and string data types. It also supports message engines like Pulsar and Kafka.
    
    <translated>
    根据提供的上下文，Milvus 是一个处理向量数据类型（如 Binary、Float32、Float16 和 BFloat16）的系统，并支持 INT64 和字符串数据类型的主键字段。它还支持 Pulsar 和 Kafka 等消息引擎。
    </translated>

