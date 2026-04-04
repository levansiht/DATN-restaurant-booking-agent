from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.permissions.permission import IsAdminPortalUser
from restaurant_booking.admin_views import _require_any_permission, _require_permission
from restaurant_booking.models import (
    Invoice,
    MenuCategory,
    MenuItem,
    Order,
    OrderItem,
    Payment,
    RestaurantProfile,
    TableSession,
)
from restaurant_booking.portal_serializers import (
    CheckoutSerializer,
    InvoiceSerializer,
    MenuCategorySerializer,
    MenuItemSerializer,
    OrderCreateSerializer,
    OrderItemCreateSerializer,
    OrderItemSerializer,
    OrderItemUpdateSerializer,
    OrderMergeSerializer,
    OrderSerializer,
    OrderSplitItemSerializer,
    OrderUpdateSerializer,
    PaymentSerializer,
    PublicMenuItemSerializer,
    PublicRestaurantProfileSerializer,
    RestaurantProfileSerializer,
    SessionMergeTableSerializer,
    SessionMoveTableSerializer,
    TableSessionCreateSerializer,
    TableSessionSerializer,
    TableSessionUpdateSerializer,
)
from restaurant_booking.services.availability import BookingValidationError
from restaurant_booking.services.internal_operations import (
    add_order_item,
    checkout_table_session,
    create_order,
    list_orders,
    list_payments,
    list_table_sessions,
    merge_orders,
    merge_table_into_session,
    move_table_in_session,
    open_table_session,
    remove_order_item,
    send_order_to_kitchen,
    split_order_item,
    update_order,
    update_order_item,
    update_table_session,
)


def _validation_error_response(exc):
    return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_restaurant_profile_detail(request):
    permission_error = _require_permission(request, "manage_restaurant_profile")
    if permission_error:
        return permission_error

    profile = RestaurantProfile.get_active_profile() or RestaurantProfile.objects.filter(
        is_deleted=False
    ).order_by("-updated_at", "-id").first()

    if request.method == "GET":
        if not profile:
            return Response({})
        return Response(RestaurantProfileSerializer(profile).data)

    serializer = RestaurantProfileSerializer(instance=profile, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    profile = serializer.save()
    return Response(RestaurantProfileSerializer(profile).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_menu_category_list_create(request):
    if request.method == "GET":
        permission_error = _require_any_permission(request, ["manage_menu", "manage_orders"])
        if permission_error:
            return permission_error
        categories = MenuCategory.objects.filter(is_deleted=False).order_by(
            "display_order",
            "name",
            "id",
        )
        return Response(MenuCategorySerializer(categories, many=True).data)

    permission_error = _require_permission(request, "manage_menu")
    if permission_error:
        return permission_error

    serializer = MenuCategorySerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    category = serializer.save()
    return Response(MenuCategorySerializer(category).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_menu_category_detail(request, category_id):
    permission_error = _require_permission(request, "manage_menu")
    if permission_error:
        return permission_error

    category = get_object_or_404(MenuCategory, id=category_id, is_deleted=False)

    if request.method == "DELETE":
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = MenuCategorySerializer(instance=category, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    category = serializer.save()
    return Response(MenuCategorySerializer(category).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_menu_item_list_create(request):
    if request.method == "GET":
        permission_error = _require_any_permission(request, ["manage_menu", "manage_orders"])
        if permission_error:
            return permission_error
        items = MenuItem.objects.filter(is_deleted=False).select_related("category").order_by(
            "name",
            "id",
        )
        query = (request.GET.get("query") or "").strip()
        status_filter = request.GET.get("status")
        category_id = request.GET.get("category")

        if query:
            items = items.filter(name__icontains=query)
        if status_filter:
            items = items.filter(status=status_filter)
        if category_id:
            items = items.filter(category_id=category_id)

        return Response(MenuItemSerializer(items, many=True).data)

    permission_error = _require_permission(request, "manage_menu")
    if permission_error:
        return permission_error

    serializer = MenuItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    item = serializer.save()
    return Response(MenuItemSerializer(item).data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_menu_item_detail(request, item_id):
    permission_error = _require_permission(request, "manage_menu")
    if permission_error:
        return permission_error

    item = get_object_or_404(MenuItem.objects.select_related("category"), id=item_id, is_deleted=False)

    if request.method == "DELETE":
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = MenuItemSerializer(instance=item, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    item = serializer.save()
    return Response(MenuItemSerializer(item).data)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_table_session_list_create(request):
    if request.method == "GET":
        permission_error = _require_any_permission(
            request,
            ["manage_tables", "manage_orders", "manage_payments"],
        )
        if permission_error:
            return permission_error

        status_filter = request.GET.get("status")
        sessions = list_table_sessions(status_filter)
        return Response(TableSessionSerializer(sessions, many=True).data)

    permission_error = _require_permission(request, "manage_tables")
    if permission_error:
        return permission_error

    serializer = TableSessionCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        session = open_table_session(
            actor=request.user,
            **serializer.validated_data,
        )
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(TableSessionSerializer(session).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_table_session_detail(request, session_id):
    permission_error = _require_any_permission(
        request,
        ["manage_tables", "manage_orders", "manage_payments"],
    )
    if permission_error:
        return permission_error

    session = get_object_or_404(
        TableSession.objects.filter(is_deleted=False),
        id=session_id,
    )

    if request.method == "GET":
        return Response(TableSessionSerializer(session).data)

    patch_permission = _require_any_permission(request, ["manage_tables", "manage_orders"])
    if patch_permission:
        return patch_permission

    serializer = TableSessionUpdateSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    try:
        session = update_table_session(session_id, **serializer.validated_data)
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(TableSessionSerializer(session).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_table_session_merge_table(request, session_id):
    permission_error = _require_permission(request, "manage_tables")
    if permission_error:
        return permission_error

    serializer = SessionMergeTableSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        session = merge_table_into_session(session_id, **serializer.validated_data)
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(TableSessionSerializer(session).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_table_session_move_table(request, session_id):
    permission_error = _require_permission(request, "manage_tables")
    if permission_error:
        return permission_error

    serializer = SessionMoveTableSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        session = move_table_in_session(session_id, **serializer.validated_data)
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(TableSessionSerializer(session).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_table_session_checkout(request, session_id):
    permission_error = _require_permission(request, "manage_payments")
    if permission_error:
        return permission_error

    serializer = CheckoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        session, payment, invoice = checkout_table_session(
            session_id,
            actor=request.user,
            **serializer.validated_data,
        )
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(
        {
            "session": TableSessionSerializer(session).data,
            "payment": PaymentSerializer(payment).data,
            "invoice": InvoiceSerializer(invoice).data if invoice else None,
        }
    )


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_order_list_create(request):
    if request.method == "GET":
        permission_error = _require_any_permission(request, ["manage_orders", "manage_payments"])
        if permission_error:
            return permission_error

        status_filter = request.GET.get("status")
        table_session_id = request.GET.get("table_session_id")
        orders = list_orders(status_filter)
        if table_session_id:
            orders = orders.filter(table_session_id=table_session_id)
        return Response(OrderSerializer(orders, many=True).data)

    permission_error = _require_permission(request, "manage_orders")
    if permission_error:
        return permission_error

    serializer = OrderCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        order = create_order(
            serializer.validated_data["table_session_id"],
            actor=request.user,
            notes=serializer.validated_data.get("notes") or "",
        )
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_order_detail(request, order_id):
    permission_error = _require_any_permission(request, ["manage_orders", "manage_payments"])
    if permission_error:
        return permission_error

    order = get_object_or_404(Order.objects.filter(is_deleted=False), id=order_id)

    if request.method == "GET":
        return Response(OrderSerializer(order).data)

    patch_permission = _require_permission(request, "manage_orders")
    if patch_permission:
        return patch_permission

    serializer = OrderUpdateSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    try:
        order = update_order(order_id, **serializer.validated_data)
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(OrderSerializer(order).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_order_send_to_kitchen(request, order_id):
    permission_error = _require_permission(request, "manage_orders")
    if permission_error:
        return permission_error

    try:
        order = send_order_to_kitchen(order_id)
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(OrderSerializer(order).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_order_item_create(request, order_id):
    permission_error = _require_permission(request, "manage_orders")
    if permission_error:
        return permission_error

    serializer = OrderItemCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        order, item = add_order_item(
            order_id,
            actor=request.user,
            **serializer.validated_data,
        )
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(
        {
            "order": OrderSerializer(order).data,
            "item": OrderItemSerializer(item).data,
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["PATCH", "DELETE"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_order_item_detail(request, order_item_id):
    permission_error = _require_permission(request, "manage_orders")
    if permission_error:
        return permission_error

    if request.method == "DELETE":
        try:
            order_id = remove_order_item(order_item_id)
        except BookingValidationError as exc:
            return _validation_error_response(exc)
        return Response({"order_id": order_id}, status=status.HTTP_200_OK)

    serializer = OrderItemUpdateSerializer(data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    try:
        item = update_order_item(order_item_id, **serializer.validated_data)
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(OrderItemSerializer(item).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_order_split_item(request, order_id):
    permission_error = _require_permission(request, "manage_orders")
    if permission_error:
        return permission_error

    serializer = OrderSplitItemSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        source_order, target_order = split_order_item(
            order_id,
            actor=request.user,
            **serializer.validated_data,
        )
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(
        {
            "source_order": OrderSerializer(source_order).data,
            "target_order": OrderSerializer(target_order).data,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_order_merge(request):
    permission_error = _require_permission(request, "manage_orders")
    if permission_error:
        return permission_error

    serializer = OrderMergeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        order = merge_orders(**serializer.validated_data)
    except BookingValidationError as exc:
        return _validation_error_response(exc)

    return Response(OrderSerializer(order).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_payment_list(request):
    permission_error = _require_any_permission(request, ["manage_payments", "view_reports"])
    if permission_error:
        return permission_error

    payments = list_payments(request.GET.get("status"))
    return Response(PaymentSerializer(payments, many=True).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated, IsAdminPortalUser])
def admin_invoice_list(request):
    permission_error = _require_any_permission(request, ["manage_payments", "view_reports"])
    if permission_error:
        return permission_error

    invoices = Invoice.objects.select_related("table_session", "payment", "issued_by").filter(
        is_deleted=False
    ).order_by("-issued_at", "-id")
    return Response(InvoiceSerializer(invoices, many=True).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def restaurant_profile_public(request):
    profile = RestaurantProfile.get_active_profile()
    if not profile:
        return Response({})
    return Response(PublicRestaurantProfileSerializer(profile).data)


@api_view(["GET"])
@permission_classes([AllowAny])
def menu_public_list(request):
    items = MenuItem.objects.filter(
        is_deleted=False,
        status=MenuItem.AvailabilityStatus.ACTIVE,
    ).select_related("category").order_by("category__display_order", "name", "id")

    query = (request.GET.get("query") or "").strip()
    if query:
        items = items.filter(name__icontains=query)

    category_id = request.GET.get("category")
    if category_id:
        items = items.filter(category_id=category_id)

    return Response(PublicMenuItemSerializer(items, many=True).data)
