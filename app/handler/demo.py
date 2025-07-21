from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
from pkg.core.result.result import success_result, error_result
from pkg.service.demo_service import get_demo_service, initialize_demo_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["demo"])


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    model: str = "gemini-2.5-flash"


class MultiTurnChatRequest(BaseModel):
    """多轮对话请求模型"""
    messages: List[Dict[str, str]]  # [{"role": "user|assistant", "content": "..."}]
    model: str = "gemini-2.5-flash"


async def get_initialized_demo_service():
    """获取已初始化的Demo服务依赖"""
    service = await get_demo_service()
    
    if not service._initialized:
        # 确保模型名称一致
        gemini_config = {
            "provider": "gemini",
            "models": {
                "gemini-2.5-flash": {  # 确保这个名称与请求中的一致
                    "api_key": os.getenv("GEMINI_API_KEY", ""),
                    "base_url": os.getenv("GEMINI_API_BASE_URL", "https://generativelanguage.googleapis.com/v1beta"),
                    "timeout": 300,
                    "max_retries": 3,
                    "max_concurrent_calls": 10
                }
            }
        }
        
        if not gemini_config["models"]["gemini-2.5-flash"]["api_key"]:
            raise HTTPException(
                status_code=500, 
                detail="Gemini API key not configured. Please set GEMINI_API_KEY environment variable."
            )
        
        try:
            await initialize_demo_service(gemini_config)
            
            # 验证初始化结果
            logger.info(f"Available providers: {service.manager.get_all_providers()}")
            logger.info(f"Available models: {service.manager.get_all_models()}")
            
        except Exception as e:
            logger.error(f"Failed to initialize demo service: {e}")
            raise HTTPException(status_code=500, detail=f"Service initialization failed: {str(e)}")
    
    return service


@router.get("/")
async def demo_info():
    """
    获取Demo API信息
    """
    return success_result(
        data={
            "message": "Welcome to LLM Demo Service",
            "description": "This service demonstrates how to use the LLM architecture to call Gemini models",
            "endpoints": {
                "GET /": "Get demo info",
                "GET /models": "Get available models",
                "POST /chat": "Simple chat with Gemini",
                "POST /chat/multi-turn": "Multi-turn conversation with Gemini"
            }
        }
    )


@router.get("/models")
async def get_models(service = Depends(get_initialized_demo_service)):
    """
    获取可用模型列表
    """
    try:
        result = await service.get_available_models()
        
        if result["success"]:
            return success_result(data=result)
        else:
            return error_result(msg=result.get("error", "Unknown error"))
            
    except Exception as e:
        logger.error(f"Failed to get models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat")
async def chat(
    request: ChatRequest,
    service = Depends(get_initialized_demo_service)
):
    """
    简单聊天接口
    
    Args:
        request: 聊天请求，包含消息和模型名称
        
    Returns:
        聊天响应
    """
    try:
        result = await service.simple_chat(
            message=request.message,
            model=request.model
        )
        
        if result["success"]:
            return success_result(data=result)
        else:
            return error_result(msg=result.get("error", "Chat failed"))
            
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/multi-turn")
async def multi_turn_chat(
    request: MultiTurnChatRequest,
    service = Depends(get_initialized_demo_service)
):
    """
    多轮对话接口
    
    Args:
        request: 多轮对话请求，包含对话历史和模型名称
        
    Returns:
        对话响应
    """
    try:
        # 验证消息格式
        for msg in request.messages:
            if "role" not in msg or "content" not in msg:
                raise HTTPException(
                    status_code=400,
                    detail="Each message must have 'role' and 'content' fields"
                )
            if msg["role"] not in ["user", "assistant"]:
                raise HTTPException(
                    status_code=400,
                    detail="Message role must be 'user' or 'assistant'"
                )
        
        result = await service.multi_turn_chat(
            messages=request.messages,
            model=request.model
        )
        
        if result["success"]:
            return success_result(data=result)
        else:
            return error_result(msg=result.get("error", "Multi-turn chat failed"))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multi-turn chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(service = Depends(get_initialized_demo_service)):
    """
    健康检查接口
    """
    try:
        # 简单的健康检查 - 验证服务是否正常初始化
        models_result = await service.get_available_models()
        
        return success_result(
            data={
                "status": "healthy",
                "service_initialized": service._initialized,
                "models_available": models_result["success"]
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return error_result(msg=f"Service unhealthy: {str(e)}") 


@router.get("/debug")
async def debug_info(service = Depends(get_initialized_demo_service)):
    """调试信息"""
    try:
        providers = service.manager.get_all_providers()
        models = service.manager.get_all_models()
        
        return success_result(data={
            "service_initialized": service._initialized,
            "providers": providers,
            "models": models,
            "total_providers": len(providers),
            "total_models": sum(len(model_list) for model_list in models.values())
        })
    except Exception as e:
        return error_result(msg=f"Debug failed: {str(e)}") 