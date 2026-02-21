"""实验服务 - Excel 存储版本"""

from datetime import datetime
from typing import Optional, List, Dict

from app.storage import excel_store
from app.core.exceptions import BadRequestException, NotFoundException
from voidview_shared import ExperimentStatus, GroupStatus


class CustomerService:
    """客户服务"""

    def __init__(self, db=None):  # db 参数保留兼容性，但不再使用
        pass

    async def get_by_id(self, customer_id: int) -> Optional[Dict]:
        """根据ID获取客户"""
        return excel_store.get_customer_by_id(customer_id)

    async def get_by_name(self, name: str) -> Optional[Dict]:
        """根据名称获取客户"""
        customers = excel_store.list_customers()
        for c in customers:
            if c["name"] == name:
                return c
        return None

    async def create(self, name: str, contact: str = None, description: str = None) -> Dict:
        """创建客户"""
        existing = await self.get_by_name(name)
        if existing:
            raise BadRequestException("客户名称已存在")
        return excel_store.create_customer(name=name, contact=contact, description=description)

    async def update(self, customer_id: int, **kwargs) -> Dict:
        """更新客户"""
        customer = await self.get_by_id(customer_id)
        if not customer:
            raise NotFoundException("客户不存在")
        result = excel_store.update_customer(customer_id, **kwargs)
        if not result:
            raise NotFoundException("客户不存在")
        return result

    async def delete(self, customer_id: int) -> None:
        """删除客户"""
        if not excel_store.delete_customer(customer_id):
            raise NotFoundException("客户不存在")

    async def list_all(self) -> List[Dict]:
        """获取所有客户"""
        return excel_store.list_customers()


class AppService:
    """应用服务"""

    def __init__(self, db=None):
        pass

    async def get_by_id(self, app_id: int) -> Optional[Dict]:
        """根据ID获取应用"""
        return excel_store.get_app_by_id(app_id)

    async def get_by_name(self, customer_id: int, name: str) -> Optional[Dict]:
        """根据名称和应用ID获取应用"""
        apps = excel_store.list_apps(customer_id=customer_id)
        for a in apps:
            if a["name"] == name:
                return a
        return None

    async def create(self, customer_id: int, name: str, description: str = None) -> Dict:
        """创建应用"""
        existing = await self.get_by_name(customer_id, name)
        if existing:
            raise BadRequestException("该客户下已存在同名应用")
        return excel_store.create_app(customer_id=customer_id, name=name, description=description)

    async def update(self, app_id: int, **kwargs) -> Dict:
        """更新应用"""
        app = await self.get_by_id(app_id)
        if not app:
            raise NotFoundException("应用不存在")
        result = excel_store.update_app(app_id, **kwargs)
        if not result:
            raise NotFoundException("应用不存在")
        return result

    async def delete(self, app_id: int) -> None:
        """删除应用"""
        if not excel_store.delete_app(app_id):
            raise NotFoundException("应用不存在")

    async def list_by_customer(self, customer_id: int) -> List[Dict]:
        """获取客户下的所有应用"""
        return excel_store.list_apps(customer_id=customer_id)


class TemplateService:
    """模板服务"""

    def __init__(self, db=None):
        pass

    async def get_by_id(self, template_id: int) -> Optional[Dict]:
        """根据ID获取模板"""
        return excel_store.get_template_by_id(template_id)

    async def get_by_name(self, app_id: int, name: str) -> Optional[Dict]:
        """根据名称和应用ID获取模板"""
        templates = excel_store.list_templates(app_id=app_id)
        for t in templates:
            if t["name"] == name:
                return t
        return None

    async def create(self, app_id: int, name: str, description: str = None) -> Dict:
        """创建模板"""
        existing = await self.get_by_name(app_id, name)
        if existing:
            raise BadRequestException("该应用下已存在同名模板")
        return excel_store.create_template(app_id=app_id, name=name, description=description)

    async def update(self, template_id: int, **kwargs) -> Dict:
        """更新模板"""
        template = await self.get_by_id(template_id)
        if not template:
            raise NotFoundException("模板不存在")
        result = excel_store.update_template(template_id, **kwargs)
        if not result:
            raise NotFoundException("模板不存在")
        return result

    async def delete(self, template_id: int) -> None:
        """删除模板"""
        if not excel_store.delete_template(template_id):
            raise NotFoundException("模板不存在")

    async def list_by_app(self, app_id: int) -> List[Dict]:
        """获取应用下的所有模板"""
        return excel_store.list_templates(app_id=app_id)


class ExperimentService:
    """实验服务"""

    def __init__(self, db=None):
        pass

    async def get_by_id(self, experiment_id: int) -> Optional[Dict]:
        """根据ID获取实验"""
        return excel_store.get_experiment_by_id(experiment_id)

    async def get_by_id_with_templates(self, experiment_id: int) -> Optional[Dict]:
        """根据ID获取实验（含关联模板）"""
        exp = await self.get_by_id(experiment_id)
        if exp:
            template_ids = excel_store.get_experiment_template_ids(experiment_id)
            exp["template_ids"] = template_ids
        return exp

    async def get_by_id_with_details(self, experiment_id: int) -> Optional[Dict]:
        """根据ID获取实验（含完整关联数据）"""
        exp = await self.get_by_id_with_templates(experiment_id)
        return exp

    async def create(
        self,
        template_ids: List[int],
        name: str,
        created_by: int,
        reference_type: str = "new"
    ) -> Dict:
        """创建实验"""
        # 验证模板是否存在
        for template_id in template_ids:
            template = await TemplateService().get_by_id(template_id)
            if not template:
                raise NotFoundException(f"模板 {template_id} 不存在")

        return excel_store.create_experiment(
            name=name,
            template_ids=template_ids,
            created_by=created_by,
            reference_type=reference_type
        )

    async def update(self, experiment_id: int, **kwargs) -> Dict:
        """更新实验"""
        experiment = await self.get_by_id(experiment_id)
        if not experiment:
            raise NotFoundException("实验不存在")

        result = excel_store.update_experiment(experiment_id, **kwargs)
        if not result:
            raise NotFoundException("实验不存在")
        return result

    async def delete(self, experiment_id: int) -> None:
        """删除实验"""
        if not excel_store.delete_experiment(experiment_id):
            raise NotFoundException("实验不存在")

    async def link_templates(self, experiment_id: int, template_ids: List[int]) -> Dict:
        """关联模板到实验"""
        experiment = await self.get_by_id(experiment_id)
        if not experiment:
            raise NotFoundException("实验不存在")

        excel_store.link_experiment_templates(experiment_id, template_ids)
        return await self.get_by_id_with_templates(experiment_id)

    async def unlink_template(self, experiment_id: int, template_id: int) -> Dict:
        """解除实验与模板的关联"""
        experiment = await self.get_by_id(experiment_id)
        if not experiment:
            raise NotFoundException("实验不存在")

        excel_store.unlink_experiment_template(experiment_id, template_id)
        return await self.get_by_id_with_templates(experiment_id)

    async def list_experiments(
        self,
        page: int = 1,
        page_size: int = 20,
        template_id: int = None,
        status: str = None
    ) -> tuple[List[Dict], int]:
        """获取实验列表"""
        return excel_store.list_experiments(
            page=page,
            page_size=page_size,
            template_id=template_id,
            status=status
        )

    async def get_matrix_data(self) -> tuple[List[Dict], List[Dict]]:
        """获取矩阵数据（用于客户矩阵页面）"""
        return excel_store.get_matrix_data()


class ExperimentGroupService:
    """实验组服务 - 简化版本"""

    def __init__(self, db=None):
        pass

    async def get_by_id(self, group_id: int) -> Optional[Dict]:
        """根据ID获取实验组"""
        return None  # 暂不实现

    async def create(self, experiment_id: int, **kwargs) -> Dict:
        """创建实验组"""
        return {"id": 1, "experiment_id": experiment_id, **kwargs}

    async def batch_create(self, experiment_id: int, groups_data: List[dict]) -> List[Dict]:
        """批量创建实验组"""
        return []

    async def update(self, group_id: int, **kwargs) -> Dict:
        """更新实验组"""
        return {"id": group_id, **kwargs}

    async def delete(self, group_id: int) -> None:
        """删除实验组"""
        pass

    async def list_by_experiment(self, experiment_id: int) -> List[Dict]:
        """获取实验下的所有实验组"""
        return []


class ObjectiveMetricsService:
    """客观指标服务 - 简化版本"""

    def __init__(self, db=None):
        pass

    async def get_by_group_id(self, group_id: int) -> Optional[Dict]:
        """根据实验组ID获取客观指标"""
        return None

    async def create_or_update(self, group_id: int, **kwargs) -> Dict:
        """创建或更新客观指标"""
        return {"id": 1, "group_id": group_id, **kwargs}
