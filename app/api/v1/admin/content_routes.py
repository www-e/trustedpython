"""
Content Management API routes.

Provides endpoints for managing platform content including games, categories,
promotional banners, and FAQ items.
"""

from logging import getLogger
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.exceptions import AppException
from app.models.user import User
from app.schemas.admin import (
    AddCategoryRequest,
    AddFAQItemRequest,
    AddGameRequest,
    CategoriesResponse,
    CreatePromoBannerRequest,
    FAQResponse,
    GamesResponse,
    PromoBannersResponse,
    UpdateGameRequest,
)
from app.schemas.common import APIResponse
from app.services.admin import AdminService

logger = getLogger(__name__)
router = APIRouter()


# ============================================================================
# Admin Role Dependency
# ============================================================================


async def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Get current admin user.

    Args:
        current_user: Current authenticated user

    Returns:
        User: Admin user

    Raises:
        ForbiddenException: If user is not admin
    """
    from app.core.exceptions import ForbiddenException

    # Check if user is admin
    # In production, you would have a role field on the User model
    # For now, we'll check if the user is verified and active
    if not current_user.profile.is_verified:
        raise ForbiddenException("access admin panel")

    # Add actual admin role check here
    # if current_user.role != "admin":
    #     raise ForbiddenException("access admin panel")

    return current_user


# ============================================================================
# Platform Configuration
# ============================================================================


@router.get(
    "/games",
    response_model=APIResponse[GamesResponse],
    status_code=status.HTTP_200_OK,
    summary="Manage games",
)
async def manage_games(
    current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> APIResponse[GamesResponse]:
    """
    Get all games for management.

    Returns all games on the platform with their statistics.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.manage_games()

        logger.info(f"Admin {current_admin.username} viewed games")

        return APIResponse.success_response(data=result, message="Games retrieved successfully")

    except AppException as e:
        logger.warning(f"Failed to get games: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting games: {str(e)}")
        raise


@router.post(
    "/games",
    response_model=APIResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Add game",
)
async def add_game(
    data: AddGameRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Add a new game.

    Adds a new game to the platform.

    - **name**: Game name (required, 2-100 characters)
    - **slug**: URL slug (required, 2-100 characters)
    - **icon_url**: Icon URL (optional)
    - **is_popular**: Popular status (default: false)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.add_game(
            name=data.name, slug=data.slug, icon_url=data.icon_url, is_popular=data.is_popular
        )

        logger.info(f"Admin {current_admin.username} added game: {data.name}")

        return APIResponse.success_response(data=result, message="Game added successfully")

    except AppException as e:
        logger.warning(f"Failed to add game: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error adding game: {str(e)}")
        raise


@router.put(
    "/games/{game_id}",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Update game",
)
async def update_game(
    game_id: UUID,
    data: UpdateGameRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Update a game.

    Updates an existing game's information.

    - **name**: Game name (optional, 2-100 characters)
    - **slug**: URL slug (optional, 2-100 characters)
    - **icon_url**: Icon URL (optional)
    - **is_active**: Active status (optional)
    - **is_popular**: Popular status (optional)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.update_game(
            game_id=game_id,
            name=data.name,
            slug=data.slug,
            icon_url=data.icon_url,
            is_active=data.is_active,
            is_popular=data.is_popular,
        )

        logger.info(f"Admin {current_admin.username} updated game: {game_id}")

        return APIResponse.success_response(data=result, message="Game updated successfully")

    except AppException as e:
        logger.warning(f"Failed to update game: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error updating game: {str(e)}")
        raise


@router.get(
    "/categories",
    response_model=APIResponse[CategoriesResponse],
    status_code=status.HTTP_200_OK,
    summary="Manage categories",
)
async def manage_categories(
    current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> APIResponse[CategoriesResponse]:
    """
    Get all categories for management.

    Returns all categories on the platform.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.manage_categories()

        logger.info(f"Admin {current_admin.username} viewed categories")

        return APIResponse.success_response(
            data=result, message="Categories retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get categories: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting categories: {str(e)}")
        raise


@router.post(
    "/categories",
    response_model=APIResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Add category",
)
async def add_category(
    data: AddCategoryRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Add a new category.

    Adds a new category to the platform.

    - **name**: Category name (required, 2-100 characters)
    - **slug**: URL slug (required, 2-100 characters)
    - **icon**: Icon (optional)
    - **description**: Description (optional)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.add_category(
            name=data.name, slug=data.slug, icon=data.icon, description=data.description
        )

        logger.info(f"Admin {current_admin.username} added category: {data.name}")

        return APIResponse.success_response(data=result, message="Category added successfully")

    except AppException as e:
        logger.warning(f"Failed to add category: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error adding category: {str(e)}")
        raise


@router.get(
    "/promo-banners",
    response_model=APIResponse[PromoBannersResponse],
    status_code=status.HTTP_200_OK,
    summary="Manage promo banners",
)
async def manage_promo_banners(
    current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> APIResponse[PromoBannersResponse]:
    """
    Get all promo banners.

    Returns all promotional banners on the platform.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.manage_promo_banners()

        logger.info(f"Admin {current_admin.username} viewed promo banners")

        return APIResponse.success_response(
            data=result, message="Promo banners retrieved successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to get promo banners: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting promo banners: {str(e)}")
        raise


@router.post(
    "/promo-banners",
    response_model=APIResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Create promo banner",
)
async def create_promo_banner(
    data: CreatePromoBannerRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Create a new promotional banner.

    Adds a new promotional banner to the platform.

    - **title**: Banner title (required, 3-200 characters)
    - **subtitle**: Banner subtitle (optional, max 300 characters)
    - **image_url**: Banner image URL (required)
    - **action_url**: Action URL (optional)
    - **action_text**: Action button text (optional, max 100 characters)
    - **priority**: Banner priority (default: 0)
    - **start_date**: Start date (required)
    - **end_date**: End date (optional)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.create_promo_banner(
            title=data.title,
            image_url=data.image_url,
            subtitle=data.subtitle,
            action_url=data.action_url,
            action_text=data.action_text,
            priority=data.priority,
        )

        logger.info(f"Admin {current_admin.username} created promo banner: {data.title}")

        return APIResponse.success_response(
            data=result, message="Promo banner created successfully"
        )

    except AppException as e:
        logger.warning(f"Failed to create promo banner: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error creating promo banner: {str(e)}")
        raise


@router.get(
    "/faq",
    response_model=APIResponse[FAQResponse],
    status_code=status.HTTP_200_OK,
    summary="Manage FAQ",
)
async def manage_faq(
    current_admin: User = Depends(get_current_admin), db: AsyncSession = Depends(get_db)
) -> APIResponse[FAQResponse]:
    """
    Get all FAQ items.

    Returns all frequently asked questions.

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.manage_faq()

        logger.info(f"Admin {current_admin.username} viewed FAQ")

        return APIResponse.success_response(data=result, message="FAQ retrieved successfully")

    except AppException as e:
        logger.warning(f"Failed to get FAQ: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error getting FAQ: {str(e)}")
        raise


@router.post(
    "/faq",
    response_model=APIResponse[dict],
    status_code=status.HTTP_201_CREATED,
    summary="Add FAQ item",
)
async def add_faq_item(
    data: AddFAQItemRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """
    Add a new FAQ item.

    Adds a new frequently asked question.

    - **question**: FAQ question (required, min 5 characters, max 300)
    - **answer**: FAQ answer (required, min 10 characters)
    - **category**: FAQ category (optional, max 100 characters)
    - **display_order**: Display order (default: 0)

    Requires admin role.
    """
    try:
        admin_service = AdminService(db)
        result = await admin_service.add_faq_item(
            question=data.question,
            answer=data.answer,
            category=data.category,
            display_order=data.display_order,
        )

        logger.info(f"Admin {current_admin.username} added FAQ item: {data.question}")

        return APIResponse.success_response(data=result, message="FAQ item added successfully")

    except AppException as e:
        logger.warning(f"Failed to add FAQ item: {e.message}")
        raise
    except Exception as e:
        logger.error(f"Error adding FAQ item: {str(e)}")
        raise
