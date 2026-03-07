"""实验管理 API 客户端"""

from typing import List, Optional

from .client import api_client, APIError
from models.experiment import (
    CustomerResponse, CustomerCreateRequest, CustomerUpdateRequest,
    AppResponse, AppCreateRequest, AppUpdateRequest,
    TemplateResponse, TemplateCreateRequest, TemplateUpdateRequest,
    ExperimentResponse, ExperimentCreateRequest, ExperimentUpdateRequest, ExperimentListResponse,
    ExperimentWithTemplatesResponse, ExperimentTemplateLinkRequest,
    ExperimentGroupResponse, ExperimentGroupCreateRequest, ExperimentGroupBatchCreateRequest,
    ExperimentGroupUpdateRequest,
    ObjectiveMetricsResponse, ObjectiveMetricsCreateRequest, ObjectiveMetricsUpdateRequest,
    MatrixResponse,
    TemplateVersionResponse, TemplateVersionCreateRequest, TemplateVersionUpdateRequest,
)


class CustomerAPI:
    """客户 API"""

    @staticmethod
    def list() -> List[CustomerResponse]:
        """获取客户列表"""
        response = api_client.get("/experiments/customers")
        return [CustomerResponse(**item) for item in response]

    @staticmethod
    def create(data: CustomerCreateRequest) -> CustomerResponse:
        """创建客户"""
        response = api_client.post("/experiments/customers", data)
        return CustomerResponse(**response)

    @staticmethod
    def get(customer_id: int) -> dict:
        """获取客户详情"""
        return api_client.get(f"/experiments/customers/{customer_id}")

    @staticmethod
    def update(customer_id: int, data: CustomerUpdateRequest) -> CustomerResponse:
        """更新客户"""
        response = api_client.put(f"/experiments/customers/{customer_id}", data)
        return CustomerResponse(**response)

    @staticmethod
    def delete(customer_id: int) -> dict:
        """删除客户"""
        return api_client.delete(f"/experiments/customers/{customer_id}")


class AppAPI:
    """应用 API"""

    @staticmethod
    def list(customer_id: int = None) -> List[AppResponse]:
        """获取应用列表"""
        params = {"customer_id": customer_id} if customer_id else None
        response = api_client.get("/experiments/apps", params=params)
        return [AppResponse(**item) for item in response]

    @staticmethod
    def create(data: AppCreateRequest) -> AppResponse:
        """创建应用"""
        response = api_client.post("/experiments/apps", data)
        return AppResponse(**response)

    @staticmethod
    def get(app_id: int) -> dict:
        """获取应用详情"""
        return api_client.get(f"/experiments/apps/{app_id}")

    @staticmethod
    def update(app_id: int, data: AppUpdateRequest) -> AppResponse:
        """更新应用"""
        response = api_client.put(f"/experiments/apps/{app_id}", data)
        return AppResponse(**response)

    @staticmethod
    def delete(app_id: int) -> dict:
        """删除应用"""
        return api_client.delete(f"/experiments/apps/{app_id}")


class TemplateAPI:
    """模板 API"""

    @staticmethod
    def list(app_id: int = None) -> List[TemplateResponse]:
        """获取模板列表"""
        params = {"app_id": app_id} if app_id else None
        response = api_client.get("/experiments/templates", params=params)
        return [TemplateResponse(**item) for item in response]

    @staticmethod
    def create(data: TemplateCreateRequest) -> TemplateResponse:
        """创建模板"""
        response = api_client.post("/experiments/templates", data)
        return TemplateResponse(**response)

    @staticmethod
    def get(template_id: int) -> dict:
        """获取模板详情"""
        return api_client.get(f"/experiments/templates/{template_id}")

    @staticmethod
    def update(template_id: int, data: TemplateUpdateRequest) -> TemplateResponse:
        """更新模板"""
        response = api_client.put(f"/experiments/templates/{template_id}", data)
        return TemplateResponse(**response)

    @staticmethod
    def delete(template_id: int) -> dict:
        """删除模板"""
        return api_client.delete(f"/experiments/templates/{template_id}")


class ExperimentAPI:
    """实验 API"""

    @staticmethod
    def list(
        page: int = 1,
        page_size: int = 20,
        template_id: int = None,
        status: str = None
    ) -> ExperimentListResponse:
        """获取实验列表"""
        params = {"page": page, "page_size": page_size}
        if template_id:
            params["template_id"] = template_id
        if status:
            params["status"] = status
        response = api_client.get("/experiments", params=params)
        return ExperimentListResponse(**response)

    @staticmethod
    def create(data: ExperimentCreateRequest) -> ExperimentResponse:
        """创建实验"""
        response = api_client.post("/experiments", data)
        return ExperimentResponse(**response)

    @staticmethod
    def get(experiment_id: int) -> ExperimentResponse:
        """获取实验详情"""
        response = api_client.get(f"/experiments/{experiment_id}")
        return ExperimentResponse(**response)

    @staticmethod
    def update(experiment_id: int, data: ExperimentUpdateRequest) -> ExperimentResponse:
        """更新实验"""
        response = api_client.put(f"/experiments/{experiment_id}", data)
        return ExperimentResponse(**response)

    @staticmethod
    def delete(experiment_id: int) -> dict:
        """删除实验"""
        return api_client.delete(f"/experiments/{experiment_id}")

    @staticmethod
    def get_matrix() -> MatrixResponse:
        """获取客户矩阵数据"""
        response = api_client.get("/experiments/matrix")
        return MatrixResponse(**response)

    @staticmethod
    def link_templates(experiment_id: int, data: ExperimentTemplateLinkRequest) -> ExperimentWithTemplatesResponse:
        """关联模板到实验"""
        response = api_client.post(f"/experiments/{experiment_id}/templates", data)
        return ExperimentWithTemplatesResponse(**response)

    @staticmethod
    def unlink_template(experiment_id: int, template_id: int) -> ExperimentWithTemplatesResponse:
        """解除实验与模板的关联"""
        response = api_client.delete(f"/experiments/{experiment_id}/templates/{template_id}")
        return ExperimentWithTemplatesResponse(**response)

    @staticmethod
    def list_groups(experiment_id: int) -> List[ExperimentGroupResponse]:
        """获取实验组列表"""
        response = api_client.get(f"/experiments/{experiment_id}/groups")
        return [ExperimentGroupResponse(**item) for item in response]

    @staticmethod
    def create_group(data: ExperimentGroupCreateRequest) -> ExperimentGroupResponse:
        """创建实验组"""
        response = api_client.post(f"/experiments/{data.experiment_id}/groups", data)
        return ExperimentGroupResponse(**response)

    @staticmethod
    def batch_create_groups(data: ExperimentGroupBatchCreateRequest) -> List[ExperimentGroupResponse]:
        """批量创建实验组"""
        response = api_client.post(f"/experiments/{data.experiment_id}/groups/batch", data)
        return [ExperimentGroupResponse(**item) for item in response]

    @staticmethod
    def update_group(group_id: int, data: ExperimentGroupUpdateRequest) -> ExperimentGroupResponse:
        """更新实验组"""
        response = api_client.put(f"/experiments/groups/{group_id}", data)
        return ExperimentGroupResponse(**response)

    @staticmethod
    def delete_group(group_id: int) -> dict:
        """删除实验组"""
        return api_client.delete(f"/experiments/groups/{group_id}")


class ObjectiveMetricsAPI:
    """客观指标 API"""

    @staticmethod
    def get(group_id: int) -> ObjectiveMetricsResponse:
        """获取客观指标"""
        response = api_client.get(f"/experiments/groups/{group_id}/metrics")
        return ObjectiveMetricsResponse(**response)

    @staticmethod
    def create_or_update(group_id: int, data: ObjectiveMetricsCreateRequest) -> ObjectiveMetricsResponse:
        """创建或更新客观指标"""
        response = api_client.post(f"/experiments/groups/{group_id}/metrics", data)
        return ObjectiveMetricsResponse(**response)

    @staticmethod
    def update(group_id: int, data: ObjectiveMetricsUpdateRequest) -> ObjectiveMetricsResponse:
        """更新客观指标"""
        response = api_client.put(f"/experiments/groups/{group_id}/metrics", data)
        return ObjectiveMetricsResponse(**response)


class TemplateVersionAPI:
    """模板版本 API"""

    @staticmethod
    def list(experiment_id: int, template_id: int) -> List[TemplateVersionResponse]:
        """获取实验-模板的版本列表"""
        response = api_client.get(f"/experiments/{experiment_id}/templates/{template_id}/versions")
        return [TemplateVersionResponse(**item) for item in response]

    @staticmethod
    def create(experiment_id: int, template_id: int, data: TemplateVersionCreateRequest) -> TemplateVersionResponse:
        """创建模板版本"""
        response = api_client.post(f"/experiments/{experiment_id}/templates/{template_id}/versions", data)
        return TemplateVersionResponse(**response)

    @staticmethod
    def update(version_id: int, data: TemplateVersionUpdateRequest) -> TemplateVersionResponse:
        """更新模板版本"""
        response = api_client.put(f"/experiments/versions/{version_id}", data)
        return TemplateVersionResponse(**response)

    @staticmethod
    def delete(version_id: int) -> dict:
        """删除模板版本"""
        return api_client.delete(f"/experiments/versions/{version_id}")

    @staticmethod
    def get_notes(experiment_id: int, template_id: int) -> str:
        """获取实验-模板关联的备注"""
        response = api_client.get(f"/experiments/{experiment_id}/templates/{template_id}/notes")
        return response.get("notes", "")

    @staticmethod
    def update_notes(experiment_id: int, template_id: int, notes: str) -> dict:
        """更新实验-模板关联的备注"""
        return api_client.put(f"/experiments/{experiment_id}/templates/{template_id}/notes", {"notes": notes})

    @staticmethod
    def get_input_files(experiment_id: int, template_id: int, target: str = "private", include_shared: bool = False) -> dict:
        """获取实验-模板关联的输入文件

        Args:
            experiment_id: 实验ID
            template_id: 模板ID
            target: 上传目标 - "shared"(共享) 或 "private"(私有)
            include_shared: 是否包含共享输入文件（当 target 为 private 时有效）
        """
        params = {"target": target}
        if include_shared:
            params["include_shared"] = "true"
        response = api_client.get(
            f"/experiments/{experiment_id}/templates/{template_id}/input-files",
            params=params
        )
        return {
            "storage_path": response.get("storage_path", ""),
            "input_files": response.get("input_files", []),
            "free_space": response.get("free_space"),  # 可能为 None
            "has_shared": response.get("has_shared", False)  # 是否有共享文件
        }

    @staticmethod
    def update_input_files(experiment_id: int, template_id: int, storage_path: str, input_files: list) -> dict:
        """更新实验-模板关联的输入文件"""
        return api_client.put(
            f"/experiments/{experiment_id}/templates/{template_id}/input-files",
            {"storage_path": storage_path, "input_files": input_files}
        )

    @staticmethod
    def upload_input_files(experiment_id: int, template_id: int, file_paths: list, target: str = "private") -> dict:
        """上传输入文件到服务端

        Args:
            experiment_id: 实验ID
            template_id: 模板ID
            file_paths: 本地文件路径列表
            target: 上传目标 - "shared"(共享) 或 "private"(私有)

        Returns:
            包含 storage_path, uploaded_files, input_files 的响应
        """
        return api_client.upload_files(
            f"/experiments/{experiment_id}/templates/{template_id}/upload-files",
            file_paths,
            params={"target": target}
        )

    @staticmethod
    def get_output_files(experiment_id: int, template_id: int, version_id: int) -> dict:
        """获取版本输出文件

        Args:
            experiment_id: 实验ID
            template_id: 模板ID
            version_id: 版本ID

        Returns:
            包含 storage_path, output_files, free_space 的响应
        """
        response = api_client.get(
            f"/experiments/{experiment_id}/templates/{template_id}/versions/{version_id}/output-files"
        )
        return {
            "storage_path": response.get("storage_path", ""),
            "output_files": response.get("output_files", []),
            "free_space": response.get("free_space")
        }

    @staticmethod
    def upload_output_files(experiment_id: int, template_id: int, version_id: int, file_paths: list) -> dict:
        """上传输出文件到服务端

        Args:
            experiment_id: 实验ID
            template_id: 模板ID
            version_id: 版本ID
            file_paths: 本地文件路径列表

        Returns:
            包含 storage_path, uploaded_files, output_files 的响应
        """
        return api_client.upload_files(
            f"/experiments/{experiment_id}/templates/{template_id}/versions/{version_id}/upload-output-files",
            file_paths
        )


# 便捷访问
customer_api = CustomerAPI()
app_api = AppAPI()
template_api = TemplateAPI()
experiment_api = ExperimentAPI()
metrics_api = ObjectiveMetricsAPI()
version_api = TemplateVersionAPI()
