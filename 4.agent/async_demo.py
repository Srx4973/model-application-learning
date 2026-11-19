from fastapi import FastAPI
from celery_app import process_large_pdf
from celery.result import AsyncResult

app = FastAPI()


# 接口 1：提交任务（注意：这里不用 async 等待，直接把任务扔进后台）
@app.post("/upload")
def upload_pdf(filename: str):
    # 用 .delay() 提交任务，它会立刻返回一个任务对象，不会阻塞程序
    task = process_large_pdf.delay(filename)

    # 立刻把任务 ID 返回给前端
    return {
        "message": "文件已接收，正在后台解析",
        "task_id": task.id
    }


# 接口 2：查询任务进度
@app.get("/status/{task_id}")
def get_task_status(task_id: str):
    # 通过 task_id 去 Redis 里查状态
    task_result = AsyncResult(task_id, app=process_large_pdf.app)

    # 1. 如果还在排队或处理中
    if task_result.state in ['PENDING', 'PROGRESS']:
        # 安全地获取 info 字典，如果是 None 就给个空字典
        info = task_result.info if isinstance(task_result.info, dict) else {}

        return {
            "state": "处理中",
            "progress": info.get('progress', 0),
            "message": info.get('message', '任务正在排队或解析中...')
        }
    # 如果处理完成了
    elif task_result.state == 'SUCCESS':
        return {
            "state": "已完成",
            "progress": 100,
            "result": task_result.result
        }
    # 如果出错了
    elif task_result.state == 'FAILURE':
        return {"state": "失败", "error": str(task_result.info)} #返回异常对象，必须转成 JSON 格式
    else:
        return {"state": "未知状态", "status": task_result.state}