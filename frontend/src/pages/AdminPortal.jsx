import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRightOnRectangleIcon,
  BanknotesIcon,
  BuildingStorefrontIcon,
  CheckCircleIcon,
  ClipboardDocumentListIcon,
  HomeModernIcon,
  ReceiptPercentIcon,
  ShieldCheckIcon,
  Squares2X2Icon,
  TableCellsIcon,
  UserGroupIcon,
  XCircleIcon,
} from "@heroicons/react/24/outline";
import {
  admin,
  auth,
  clearAdminAuthTokens,
  getAdminRefreshToken,
} from "../api";
import { ADMIN_LOGIN_PATH, GUEST_HOME_PATH } from "../constants/routes.js";
import { useRestaurantRealtime } from "../hooks/useRestaurantRealtime.js";


const EMPTY_TABLE_FORM = {
  table_type: "INDOOR",
  capacity: 2,
  floor: 1,
  status: "AVAILABLE",
  width: "",
  length: "",
  notes: "",
};

const PERMISSION_OPTIONS = [
  { key: "manage_restaurant_profile", label: "Thông tin nhà hàng" },
  { key: "manage_bookings", label: "Booking" },
  { key: "manage_tables", label: "Bàn" },
  { key: "manage_menu", label: "Menu" },
  { key: "manage_orders", label: "Order" },
  { key: "manage_payments", label: "Thanh toán" },
  { key: "manage_team", label: "Nhân sự" },
  { key: "view_reports", label: "Báo cáo" },
];

const INTERNAL_ROLE_OPTIONS = [
  { value: "ADMIN", label: "Admin" },
  { value: "WAITER", label: "Waiter" },
  { value: "CASHIER", label: "Cashier" },
];

function createEmptyPermissions() {
  return PERMISSION_OPTIONS.reduce((accumulator, permission) => {
    accumulator[permission.key] = false;
    return accumulator;
  }, {});
}

function buildPermissionState(role = "ADMIN", overrides = {}) {
  const basePermissions = createEmptyPermissions();
  const defaultsByRole = {
    ADMIN: {
      ...basePermissions,
      manage_restaurant_profile: true,
      manage_bookings: true,
      manage_tables: true,
      manage_menu: true,
      manage_orders: true,
      manage_payments: true,
    },
    WAITER: {
      ...basePermissions,
      manage_tables: true,
      manage_orders: true,
    },
    CASHIER: {
      ...basePermissions,
      manage_orders: true,
      manage_payments: true,
    },
    SUPER_ADMIN: PERMISSION_OPTIONS.reduce((accumulator, permission) => {
      accumulator[permission.key] = true;
      return accumulator;
    }, {}),
  };

  const normalizedOverrides = PERMISSION_OPTIONS.reduce((accumulator, permission) => {
    if (Object.prototype.hasOwnProperty.call(overrides, permission.key)) {
      accumulator[permission.key] = Boolean(overrides[permission.key]);
    }
    return accumulator;
  }, {});

  return {
    ...(defaultsByRole[role] || basePermissions),
    ...normalizedOverrides,
  };
}

function createEmptyTeamForm() {
  return {
    email: "",
    full_name: "",
    password: "",
    phone_number: "",
    role: "ADMIN",
    status: "ACTIVE",
    admin_permissions: buildPermissionState("ADMIN"),
  };
}

function parseCommaSeparatedIds(value) {
  return String(value || "")
    .split(",")
    .map((item) => Number(item.trim()))
    .filter((item) => Number.isInteger(item) && item > 0);
}

function createEmptyRestaurantProfileForm() {
  return {
    name: "",
    description: "",
    phone_number: "",
    email: "",
    address: "",
    opening_time: "10:00",
    closing_time: "22:00",
    website: "",
    ai_greeting: "",
    price_range_min: "",
    price_range_max: "",
    is_active: true,
  };
}

function createEmptyCategoryForm() {
  return {
    name: "",
    description: "",
    display_order: 0,
    is_active: true,
    default_image_url: "",
    default_image_alt_text: "",
  };
}

function createEmptyMenuItemForm() {
  return {
    category: "",
    name: "",
    description: "",
    price: "",
    status: "ACTIVE",
    is_recommended: false,
    is_vegetarian: false,
    is_best_seller: false,
    is_kid_friendly: false,
    image_url: "",
    image_alt_text: "",
    is_illustration: false,
    spicy_level: "NONE",
    tags_input: "",
    dietary_labels_input: "",
    preparation_time_minutes: "",
    serving_start_time: "",
    serving_end_time: "",
    suggested_pairings: [],
  };
}

function parseCommaSeparatedList(value) {
  return String(value || "")
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

function stringifyCommaSeparatedList(values) {
  return (values || []).join(", ");
}

function createEmptySessionForm() {
  return {
    table_ids: "",
    guest_name: "",
    guest_phone: "",
    guest_count: 1,
    booking_id: "",
    notes: "",
  };
}

function createEmptyOrderForm() {
  return {
    table_session_id: "",
    notes: "",
  };
}

function createEmptyOrderItemForm() {
  return {
    order_id: "",
    menu_item_id: "",
    quantity: 1,
    note: "",
  };
}

function createEmptyMergeTableForm() {
  return {
    session_id: "",
    table_id: "",
  };
}

function createEmptyMoveTableForm() {
  return {
    session_id: "",
    from_table_id: "",
    to_table_id: "",
  };
}

function createEmptySplitItemForm() {
  return {
    order_id: "",
    order_item_id: "",
    quantity: 1,
    target_order_id: "",
  };
}

function createEmptyMergeOrdersForm() {
  return {
    source_order_id: "",
    target_order_id: "",
  };
}

function createEmptyCheckoutForm() {
  return {
    session_id: "",
    method: "CASH",
    issue_invoice: true,
    note: "",
  };
}


function getErrorMessage(error) {
  const responseData = error?.response?.data;
  if (responseData && typeof responseData === "object") {
    const dynamicError = Object.values(responseData).find((value) => {
      if (Array.isArray(value)) {
        return value[0];
      }
      return typeof value === "string" && value;
    });

    if (Array.isArray(dynamicError)) {
      return dynamicError[0];
    }
    if (typeof dynamicError === "string") {
      return dynamicError;
    }
  }

  return (
    error?.response?.data?.table_id?.[0] ||
    error?.response?.data?.party_size?.[0] ||
    error?.response?.data?.message ||
    error?.response?.data?.detail ||
    error?.response?.data?.error ||
    "Đã xảy ra lỗi, vui lòng thử lại."
  );
}


function getTableStatusTone(status) {
  if (status === "AVAILABLE") {
    return "success";
  }

  if (status === "RESERVED") {
    return "warning";
  }

  if (status === "OCCUPIED" || status === "MAINTENANCE") {
    return "danger";
  }

  return "default";
}


function StatusBadge({ children, tone = "default" }) {
  const toneClasses = {
    success: "border-emerald-200 bg-emerald-50 text-emerald-700",
    warning: "border-amber-200 bg-amber-50 text-amber-700",
    danger: "border-rose-200 bg-rose-50 text-rose-700",
    default: "border-stone-200 bg-stone-100 text-stone-700",
  };

  return (
    <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${toneClasses[tone]}`}>
      {children}
    </span>
  );
}


const AdminPortal = () => {
  const navigate = useNavigate();
  const [session, setSession] = useState(null);
  const [summary, setSummary] = useState(null);
  const [bookings, setBookings] = useState([]);
  const [tables, setTables] = useState([]);
  const [restaurantProfile, setRestaurantProfile] = useState(null);
  const [profileForm, setProfileForm] = useState(createEmptyRestaurantProfileForm);
  const [menuCategories, setMenuCategories] = useState([]);
  const [menuItems, setMenuItems] = useState([]);
  const [categoryForm, setCategoryForm] = useState(createEmptyCategoryForm);
  const [itemForm, setItemForm] = useState(createEmptyMenuItemForm);
  const [editingCategoryId, setEditingCategoryId] = useState(null);
  const [editingMenuItemId, setEditingMenuItemId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [payments, setPayments] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [sessionForm, setSessionForm] = useState(createEmptySessionForm);
  const [orderForm, setOrderForm] = useState(createEmptyOrderForm);
  const [orderItemForm, setOrderItemForm] = useState(createEmptyOrderItemForm);
  const [mergeTableForm, setMergeTableForm] = useState(createEmptyMergeTableForm);
  const [moveTableForm, setMoveTableForm] = useState(createEmptyMoveTableForm);
  const [splitItemForm, setSplitItemForm] = useState(createEmptySplitItemForm);
  const [mergeOrdersForm, setMergeOrdersForm] = useState(createEmptyMergeOrdersForm);
  const [checkoutForm, setCheckoutForm] = useState(createEmptyCheckoutForm);
  const [teamUsers, setTeamUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sectionLoading, setSectionLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeSection, setActiveSection] = useState("overview");
  const [bookingFilters, setBookingFilters] = useState({
    query: "",
    status: "",
  });
  const [tableForm, setTableForm] = useState(EMPTY_TABLE_FORM);
  const [editingTableId, setEditingTableId] = useState(null);
  const [teamForm, setTeamForm] = useState(createEmptyTeamForm);
  const [editingUserId, setEditingUserId] = useState(null);
  const sessionRef = useRef(null);
  const loadPortalDataRef = useRef(null);
  const queueRealtimeRefreshRef = useRef(null);
  const realtimeRefreshInFlightRef = useRef(false);
  const pendingRealtimeRefreshRef = useRef(false);

  const bookingAccess = session?.admin_permissions?.manage_bookings;
  const tableAccess = session?.admin_permissions?.manage_tables;
  const profileAccess = session?.admin_permissions?.manage_restaurant_profile;
  const menuAccess = session?.admin_permissions?.manage_menu;
  const orderAccess = session?.admin_permissions?.manage_orders;
  const paymentAccess = session?.admin_permissions?.manage_payments;
  const reportAccess = session?.admin_permissions?.view_reports;
  const isSuperAdmin = session?.role === "SUPER_ADMIN";

  const loadBookings = async (filters = bookingFilters, currentSession = session) => {
    if (!currentSession?.admin_permissions?.manage_bookings) {
      return;
    }
    const response = await admin.getBookings({
      page_size: 50,
      query: filters.query || undefined,
      status: filters.status || undefined,
    });
    setBookings(response.data?.results || []);
  };

  const loadTables = async (currentSession = session) => {
    if (!currentSession?.admin_permissions?.manage_tables) {
      return;
    }
    const response = await admin.getTables();
    setTables(response.data || []);
  };

  const loadRestaurantProfile = async (currentSession = session) => {
    if (!currentSession?.admin_permissions?.manage_restaurant_profile) {
      return;
    }
    const response = await admin.getRestaurantProfile();
    const profileData = response.data || {};
    setRestaurantProfile(profileData);
    setProfileForm({
      ...createEmptyRestaurantProfileForm(),
      ...profileData,
      opening_time: profileData.opening_time?.slice?.(0, 5) || "10:00",
      closing_time: profileData.closing_time?.slice?.(0, 5) || "22:00",
      price_range_min: profileData.price_range_min ?? "",
      price_range_max: profileData.price_range_max ?? "",
    });
  };

  const loadMenuData = async (currentSession = session) => {
    if (!currentSession?.admin_permissions?.manage_menu && !currentSession?.admin_permissions?.manage_orders) {
      return;
    }

    const [categoriesResponse, itemsResponse] = await Promise.all([
      admin.getMenuCategories(),
      admin.getMenuItems(),
    ]);
    setMenuCategories(categoriesResponse.data || []);
    setMenuItems(itemsResponse.data || []);
  };

  const loadSessions = async (currentSession = session) => {
    if (
      !currentSession?.admin_permissions?.manage_tables &&
      !currentSession?.admin_permissions?.manage_orders &&
      !currentSession?.admin_permissions?.manage_payments
    ) {
      return;
    }
    const response = await admin.getSessions({ status: "" });
    setSessions(response.data || []);
  };

  const loadPaymentsData = async (currentSession = session) => {
    if (
      !currentSession?.admin_permissions?.manage_payments &&
      !currentSession?.admin_permissions?.view_reports
    ) {
      return;
    }
    const [paymentsResponse, invoicesResponse] = await Promise.all([
      admin.getPayments(),
      admin.getInvoices(),
    ]);
    setPayments(paymentsResponse.data || []);
    setInvoices(invoicesResponse.data || []);
  };

  const loadTeamUsers = async () => {
    if (!isSuperAdmin) {
      return;
    }
    const response = await admin.getAdminUsers();
    setTeamUsers(response.data || []);
  };

  const loadPortalData = async (currentSession, { showLoading = true } = {}) => {
    if (!currentSession) {
      return;
    }

    if (showLoading) {
      setSectionLoading(true);
    }

    try {
      const summaryResponse = await admin.getDashboardSummary();
      setSummary(summaryResponse.data);

      if (currentSession.admin_permissions?.manage_bookings) {
        await loadBookings(bookingFilters, currentSession);
      }

      if (currentSession.admin_permissions?.manage_tables) {
        await loadTables(currentSession);
      }

      if (currentSession.admin_permissions?.manage_restaurant_profile) {
        await loadRestaurantProfile(currentSession);
      }

      if (
        currentSession.admin_permissions?.manage_menu ||
        currentSession.admin_permissions?.manage_orders
      ) {
        await loadMenuData(currentSession);
      }

      if (
        currentSession.admin_permissions?.manage_tables ||
        currentSession.admin_permissions?.manage_orders ||
        currentSession.admin_permissions?.manage_payments
      ) {
        await loadSessions(currentSession);
      }

      if (
        currentSession.admin_permissions?.manage_payments ||
        currentSession.admin_permissions?.view_reports
      ) {
        await loadPaymentsData(currentSession);
      }

      if (currentSession.role === "SUPER_ADMIN") {
        const teamResponse = await admin.getAdminUsers();
        setTeamUsers(teamResponse.data || []);
      }
    } finally {
      if (showLoading) {
        setSectionLoading(false);
      }
    }
  };

  loadPortalDataRef.current = loadPortalData;

  useEffect(() => {
    sessionRef.current = session;
  }, [session]);

  useEffect(() => {
    let mounted = true;

    const bootstrap = async () => {
      setLoading(true);
      setError("");
      try {
        const response = await admin.getSession();
        if (!mounted) {
          return;
        }

        setSession(response.data);
        sessionRef.current = response.data;
        await loadPortalDataRef.current?.(response.data);
      } catch {
        if (!mounted) {
          return;
        }
        clearAdminAuthTokens();
        navigate(ADMIN_LOGIN_PATH, { replace: true });
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    bootstrap();

    return () => {
      mounted = false;
    };
  }, [navigate]);

  const queueRealtimeRefresh = async () => {
    const currentSession = sessionRef.current;
    if (!currentSession) {
      return;
    }

    if (realtimeRefreshInFlightRef.current) {
      pendingRealtimeRefreshRef.current = true;
      return;
    }

    realtimeRefreshInFlightRef.current = true;

    try {
      await loadPortalData(currentSession, { showLoading: false });
    } catch (realtimeError) {
      console.error(realtimeError);
    } finally {
      realtimeRefreshInFlightRef.current = false;
      if (pendingRealtimeRefreshRef.current) {
        pendingRealtimeRefreshRef.current = false;
        void queueRealtimeRefresh();
      }
    }
  };

  queueRealtimeRefreshRef.current = queueRealtimeRefresh;

  const refreshPortalSnapshot = async () => {
    const currentSession = sessionRef.current;
    if (!currentSession) {
      return;
    }

    await loadPortalData(currentSession, { showLoading: false });
  };

  const { isConnected: isRealtimeConnected } = useRestaurantRealtime({
    enabled: Boolean(session),
    onEvent: (event) => {
      if (event?.domain !== "restaurant_booking") {
        return;
      }
      queueRealtimeRefresh();
    },
  });

  useEffect(() => {
    if (!session || isRealtimeConnected) {
      return undefined;
    }

    const refreshPortalData = () => {
      if (document.visibilityState !== "visible") {
        return;
      }

      void queueRealtimeRefreshRef.current?.();
    };

    const intervalId = window.setInterval(refreshPortalData, 5000);
    document.addEventListener("visibilitychange", refreshPortalData);

    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", refreshPortalData);
    };
  }, [isRealtimeConnected, session]);

  const handleLogout = async () => {
    try {
      const refreshToken = getAdminRefreshToken();
      if (refreshToken) {
        await auth.logout(refreshToken);
      }
    } catch (logoutError) {
      console.error(logoutError);
    } finally {
      clearAdminAuthTokens();
      navigate(ADMIN_LOGIN_PATH, { replace: true });
    }
  };

  const handleBookingFilterChange = (event) => {
    const { name, value } = event.target;
    setBookingFilters((prev) => ({ ...prev, [name]: value }));
  };

  const handleBookingSearch = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      await loadBookings();
    } catch (searchError) {
      setError(getErrorMessage(searchError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleBookingAction = async (bookingId, nextStatus) => {
    const payload = { status: nextStatus };

    if (nextStatus === "CANCELLED") {
      payload.cancellation_reason =
        window.prompt("Lý do hủy booking này:", "Khách thay đổi kế hoạch") || "";
    }

    setSectionLoading(true);
    setError("");
    try {
      await admin.updateBookingStatus(bookingId, payload);
      await loadBookings();
      const summaryResponse = await admin.getDashboardSummary();
      setSummary(summaryResponse.data);
    } catch (actionError) {
      setError(getErrorMessage(actionError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleTableFormChange = (event) => {
    const { name, value } = event.target;
    setTableForm((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const resetTableForm = () => {
    setTableForm(EMPTY_TABLE_FORM);
    setEditingTableId(null);
  };

  const submitTableForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      const payload = {
        ...tableForm,
        capacity: Number(tableForm.capacity),
        floor: Number(tableForm.floor),
        width: tableForm.width || null,
        length: tableForm.length || null,
        notes: tableForm.notes || "",
      };

      if (editingTableId) {
        await admin.updateTable(editingTableId, payload);
      } else {
        await admin.createTable(payload);
      }

      resetTableForm();
      await loadTables();
      const summaryResponse = await admin.getDashboardSummary();
      setSummary(summaryResponse.data);
    } catch (tableError) {
      setError(getErrorMessage(tableError));
    } finally {
      setSectionLoading(false);
    }
  };

  const editTable = (table) => {
    setEditingTableId(table.id);
    setTableForm({
      table_type: table.table_type,
      capacity: table.capacity,
      floor: table.floor,
      status: table.status,
      width: table.width || "",
      length: table.length || "",
      notes: table.notes || "",
    });
    setActiveSection("tables");
  };

  const handleQuickTableStatus = async (tableId, nextStatus) => {
    setSectionLoading(true);
    setError("");
    try {
      await admin.updateTable(tableId, { status: nextStatus });
      await refreshPortalSnapshot();
    } catch (tableError) {
      setError(getErrorMessage(tableError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleReleaseTable = async (tableId) => {
    setSectionLoading(true);
    setError("");
    try {
      await admin.releaseTable(tableId);
      await refreshPortalSnapshot();
    } catch (tableError) {
      setError(getErrorMessage(tableError));
    } finally {
      setSectionLoading(false);
    }
  };

  const removeTable = async (tableId) => {
    if (!window.confirm("Xóa bàn này khỏi hệ thống?")) {
      return;
    }

    setSectionLoading(true);
    setError("");
    try {
      await admin.deleteTable(tableId);
      await loadTables();
    } catch (tableError) {
      setError(getErrorMessage(tableError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleTeamFormChange = (event) => {
    const { name, value } = event.target;
    if (name === "role") {
      setTeamForm((prev) => ({
        ...prev,
        role: value,
        admin_permissions: buildPermissionState(value),
      }));
      return;
    }

    setTeamForm((prev) => ({ ...prev, [name]: value }));
  };

  const handlePermissionToggle = (permissionKey) => {
    setTeamForm((prev) => ({
      ...prev,
      admin_permissions: {
        ...prev.admin_permissions,
        [permissionKey]: !prev.admin_permissions[permissionKey],
      },
    }));
  };

  const resetTeamForm = () => {
    setTeamForm(createEmptyTeamForm());
    setEditingUserId(null);
  };

  const submitTeamForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");

    const payload = {
      ...teamForm,
      phone_number: teamForm.phone_number || null,
      admin_permissions: teamForm.admin_permissions,
    };

    if (!payload.password) {
      delete payload.password;
    }

    try {
      if (editingUserId) {
        await admin.updateAdminUser(editingUserId, payload);
      } else {
        await admin.createAdminUser(payload);
      }
      resetTeamForm();
      await loadTeamUsers();
    } catch (teamError) {
      setError(getErrorMessage(teamError));
    } finally {
      setSectionLoading(false);
    }
  };

  const editUser = (user) => {
    setEditingUserId(user.id);
    setTeamForm({
      email: user.email,
      full_name: user.full_name || "",
      password: "",
      phone_number: user.phone_number || "",
      role: user.role === "SUPER_ADMIN" ? "ADMIN" : user.role,
      status: user.status,
      admin_permissions: buildPermissionState(user.role, user.admin_permissions || {}),
    });
    setActiveSection("team");
  };

  const removeUser = async (userId) => {
    if (!window.confirm("Xóa tài khoản nhân sự này?")) {
      return;
    }
    setSectionLoading(true);
    setError("");
    try {
      await admin.deleteAdminUser(userId);
      await loadTeamUsers();
    } catch (teamError) {
      setError(getErrorMessage(teamError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleProfileFormChange = (event) => {
    const { name, value, type, checked } = event.target;
    setProfileForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const submitProfileForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      const payload = {
        ...profileForm,
        price_range_min: profileForm.price_range_min || null,
        price_range_max: profileForm.price_range_max || null,
      };
      await admin.updateRestaurantProfile(payload);
      await loadRestaurantProfile();
    } catch (profileError) {
      setError(getErrorMessage(profileError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleCategoryFormChange = (event) => {
    const { name, value, type, checked } = event.target;
    setCategoryForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const resetCategoryForm = () => {
    setCategoryForm(createEmptyCategoryForm());
    setEditingCategoryId(null);
  };

  const editCategory = (category) => {
    setEditingCategoryId(category.id);
    setCategoryForm({
      name: category.name || "",
      description: category.description || "",
      display_order: category.display_order ?? 0,
      is_active: Boolean(category.is_active),
      default_image_url: category.default_image_url || "",
      default_image_alt_text: category.default_image_alt_text || "",
    });
    setActiveSection("menu");
  };

  const submitCategoryForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      const payload = {
        ...categoryForm,
        display_order: Number(categoryForm.display_order || 0),
        default_image_url: categoryForm.default_image_url || null,
        default_image_alt_text: categoryForm.default_image_alt_text || null,
      };
      if (editingCategoryId) {
        await admin.updateMenuCategory(editingCategoryId, payload);
      } else {
        await admin.createMenuCategory(payload);
      }
      resetCategoryForm();
      await loadMenuData();
    } catch (menuError) {
      setError(getErrorMessage(menuError));
    } finally {
      setSectionLoading(false);
    }
  };

  const removeCategory = async (categoryId) => {
    if (!window.confirm("Xóa danh mục này?")) {
      return;
    }
    setSectionLoading(true);
    setError("");
    try {
      await admin.deleteMenuCategory(categoryId);
      await loadMenuData();
    } catch (menuError) {
      setError(getErrorMessage(menuError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleItemFormChange = (event) => {
    const { name, value, type, checked, selectedOptions } = event.target;
    setItemForm((prev) => ({
      ...prev,
      [name]:
        type === "checkbox"
          ? checked
          : type === "select-multiple"
            ? Array.from(selectedOptions || []).map((option) => option.value)
            : value,
    }));
  };

  const resetMenuItemForm = () => {
    setItemForm(createEmptyMenuItemForm());
    setEditingMenuItemId(null);
  };

  const editMenuItem = (item) => {
    setEditingMenuItemId(item.id);
    setItemForm({
      category: item.category || "",
      name: item.name || "",
      description: item.description || "",
      price: item.price ?? "",
      status: item.status || "ACTIVE",
      is_recommended: Boolean(item.is_recommended),
      is_vegetarian: Boolean(item.is_vegetarian),
      is_best_seller: Boolean(item.is_best_seller),
      is_kid_friendly: Boolean(item.is_kid_friendly),
      image_url: item.image_url || "",
      image_alt_text: item.image_alt_text || "",
      is_illustration: Boolean(item.is_illustration),
      spicy_level: item.spicy_level || "NONE",
      tags_input: stringifyCommaSeparatedList(item.tags),
      dietary_labels_input: stringifyCommaSeparatedList(item.dietary_labels),
      preparation_time_minutes: item.preparation_time_minutes ?? "",
      serving_start_time: item.serving_start_time?.slice?.(0, 5) || "",
      serving_end_time: item.serving_end_time?.slice?.(0, 5) || "",
      suggested_pairings: (item.suggested_pairings || []).map((pairingId) => String(pairingId)),
    });
    setActiveSection("menu");
  };

  const submitMenuItemForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      const payload = {
        ...itemForm,
        category: itemForm.category || null,
        price: Number(itemForm.price),
        preparation_time_minutes: itemForm.preparation_time_minutes
          ? Number(itemForm.preparation_time_minutes)
          : null,
        image_url: itemForm.image_url || null,
        image_alt_text: itemForm.image_alt_text || null,
        tags: parseCommaSeparatedList(itemForm.tags_input),
        dietary_labels: parseCommaSeparatedList(itemForm.dietary_labels_input),
        serving_start_time: itemForm.serving_start_time || null,
        serving_end_time: itemForm.serving_end_time || null,
        suggested_pairings: itemForm.suggested_pairings.map((pairingId) => Number(pairingId)),
      };
      delete payload.tags_input;
      delete payload.dietary_labels_input;
      if (editingMenuItemId) {
        await admin.updateMenuItem(editingMenuItemId, payload);
      } else {
        await admin.createMenuItem(payload);
      }
      resetMenuItemForm();
      await loadMenuData();
    } catch (menuError) {
      setError(getErrorMessage(menuError));
    } finally {
      setSectionLoading(false);
    }
  };

  const removeMenuItem = async (itemId) => {
    if (!window.confirm("Xóa món này khỏi menu?")) {
      return;
    }
    setSectionLoading(true);
    setError("");
    try {
      await admin.deleteMenuItem(itemId);
      await loadMenuData();
    } catch (menuError) {
      setError(getErrorMessage(menuError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleSessionFormChange = (event) => {
    const { name, value } = event.target;
    setSessionForm((prev) => ({ ...prev, [name]: value }));
  };

  const submitSessionForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      await admin.createSession({
        table_ids: parseCommaSeparatedIds(sessionForm.table_ids),
        guest_name: sessionForm.guest_name || null,
        guest_phone: sessionForm.guest_phone || null,
        guest_count: Number(sessionForm.guest_count || 1),
        booking_id: sessionForm.booking_id ? Number(sessionForm.booking_id) : null,
        notes: sessionForm.notes || "",
      });
      setSessionForm(createEmptySessionForm());
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleOrderFormChange = (event) => {
    const { name, value } = event.target;
    setOrderForm((prev) => ({ ...prev, [name]: value }));
  };

  const submitOrderForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      await admin.createOrder({
        table_session_id: Number(orderForm.table_session_id),
        notes: orderForm.notes || "",
      });
      setOrderForm(createEmptyOrderForm());
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleOrderItemFormChange = (event) => {
    const { name, value } = event.target;
    setOrderItemForm((prev) => ({ ...prev, [name]: value }));
  };

  const submitOrderItemForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      await admin.addOrderItem(Number(orderItemForm.order_id), {
        menu_item_id: Number(orderItemForm.menu_item_id),
        quantity: Number(orderItemForm.quantity || 1),
        note: orderItemForm.note || "",
      });
      setOrderItemForm(createEmptyOrderItemForm());
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleMergeTableFormChange = (event) => {
    const { name, value } = event.target;
    setMergeTableForm((prev) => ({ ...prev, [name]: value }));
  };

  const submitMergeTableForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      await admin.mergeTableIntoSession(Number(mergeTableForm.session_id), {
        table_id: Number(mergeTableForm.table_id),
      });
      setMergeTableForm(createEmptyMergeTableForm());
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleMoveTableFormChange = (event) => {
    const { name, value } = event.target;
    setMoveTableForm((prev) => ({ ...prev, [name]: value }));
  };

  const submitMoveTableForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      await admin.moveTableInSession(Number(moveTableForm.session_id), {
        from_table_id: Number(moveTableForm.from_table_id),
        to_table_id: Number(moveTableForm.to_table_id),
      });
      setMoveTableForm(createEmptyMoveTableForm());
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleSplitItemFormChange = (event) => {
    const { name, value } = event.target;
    setSplitItemForm((prev) => ({ ...prev, [name]: value }));
  };

  const submitSplitItemForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      await admin.splitOrderItem(Number(splitItemForm.order_id), {
        order_item_id: Number(splitItemForm.order_item_id),
        quantity: Number(splitItemForm.quantity || 1),
        target_order_id: splitItemForm.target_order_id
          ? Number(splitItemForm.target_order_id)
          : null,
      });
      setSplitItemForm(createEmptySplitItemForm());
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleMergeOrdersFormChange = (event) => {
    const { name, value } = event.target;
    setMergeOrdersForm((prev) => ({ ...prev, [name]: value }));
  };

  const submitMergeOrdersForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      await admin.mergeOrders({
        source_order_id: Number(mergeOrdersForm.source_order_id),
        target_order_id: Number(mergeOrdersForm.target_order_id),
      });
      setMergeOrdersForm(createEmptyMergeOrdersForm());
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleCheckoutFormChange = (event) => {
    const { name, value, type, checked } = event.target;
    setCheckoutForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const submitCheckoutForm = async (event) => {
    event.preventDefault();
    setSectionLoading(true);
    setError("");
    try {
      await admin.checkoutSession(Number(checkoutForm.session_id), {
        method: checkoutForm.method,
        issue_invoice: Boolean(checkoutForm.issue_invoice),
        note: checkoutForm.note || "",
      });
      setCheckoutForm(createEmptyCheckoutForm());
      await refreshPortalSnapshot();
    } catch (paymentError) {
      setError(getErrorMessage(paymentError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleSendOrderToKitchen = async (orderId) => {
    setSectionLoading(true);
    setError("");
    try {
      await admin.sendOrderToKitchen(orderId);
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleDeleteOrderItem = async (orderItemId) => {
    if (!window.confirm("Xóa món này khỏi order?")) {
      return;
    }
    setSectionLoading(true);
    setError("");
    try {
      await admin.deleteOrderItem(orderItemId);
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleEditOrderItem = async (item) => {
    const nextQuantity = window.prompt("Cập nhật số lượng", String(item.quantity));
    if (nextQuantity === null) {
      return;
    }
    const nextNote = window.prompt("Ghi chú món", item.note || "");
    setSectionLoading(true);
    setError("");
    try {
      await admin.updateOrderItem(item.id, {
        quantity: Number(nextQuantity),
        note: nextNote || "",
      });
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleQuickCreateOrder = async (sessionId) => {
    setSectionLoading(true);
    setError("");
    try {
      await admin.createOrder({ table_session_id: sessionId, notes: "" });
      await refreshPortalSnapshot();
    } catch (operationError) {
      setError(getErrorMessage(operationError));
    } finally {
      setSectionLoading(false);
    }
  };

  const handleQuickCheckout = async (sessionId) => {
    const method = window.prompt("Phương thức: CASH, BANK_TRANSFER hoặc CARD", "CASH");
    if (!method) {
      return;
    }
    setSectionLoading(true);
    setError("");
    try {
      await admin.checkoutSession(sessionId, {
        method,
        issue_invoice: true,
        note: "",
      });
      await refreshPortalSnapshot();
    } catch (paymentError) {
      setError(getErrorMessage(paymentError));
    } finally {
      setSectionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-stone-100">
        <div className="rounded-3xl border border-stone-200 bg-white px-6 py-5 text-sm text-stone-600 shadow-lg">
          Đang tải cổng quản trị...
        </div>
      </div>
    );
  }

  const flattenedOrders = sessions.flatMap((sessionItem) =>
    (sessionItem.orders || []).map((order) => ({
      ...order,
      table_session_code: sessionItem.code,
      table_session_id: sessionItem.id,
    }))
  );

  const navigationItems = [
    { id: "overview", label: "Tổng quan", icon: Squares2X2Icon, enabled: true },
    { id: "profile", label: "Nhà hàng", icon: BuildingStorefrontIcon, enabled: profileAccess },
    { id: "menu", label: "Menu", icon: ClipboardDocumentListIcon, enabled: menuAccess || orderAccess },
    { id: "bookings", label: "Đặt bàn", icon: ClipboardDocumentListIcon, enabled: bookingAccess },
    { id: "tables", label: "Bàn ăn", icon: TableCellsIcon, enabled: tableAccess },
    { id: "operations", label: "Vận hành", icon: TableCellsIcon, enabled: orderAccess || tableAccess || paymentAccess },
    { id: "payments", label: "Thanh toán", icon: BanknotesIcon, enabled: paymentAccess || reportAccess },
    { id: "team", label: "Nhân sự", icon: UserGroupIcon, enabled: isSuperAdmin },
  ];

  return (
    <div className="min-h-screen bg-[#f3efe7]">
      <div className="grid min-h-screen lg:grid-cols-[280px_1fr]">
        <aside className="border-r border-stone-200 bg-[#16322c] px-6 py-8 text-white">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
            <div className="flex items-center gap-3 text-xs uppercase tracking-[0.25em] text-emerald-200/80">
              <ShieldCheckIcon className="h-5 w-5" />
              PSCD Internal
            </div>
            <h1 className="mt-5 text-2xl font-semibold">{session?.full_name || session?.email}</h1>
            <div className="mt-3 flex items-center gap-2">
              <StatusBadge tone={isSuperAdmin ? "success" : "warning"}>
                {session?.role}
              </StatusBadge>
              <StatusBadge>{session?.status}</StatusBadge>
            </div>
            <p className="mt-4 text-sm leading-6 text-emerald-50/75">{session?.email}</p>
          </div>

          <nav className="mt-8 space-y-2">
            {navigationItems.map((item) => (
              <button
                key={item.id}
                type="button"
                disabled={!item.enabled}
                onClick={() => item.enabled && setActiveSection(item.id)}
                className={`flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm font-medium transition ${
                  activeSection === item.id
                    ? "bg-white text-[#16322c]"
                    : item.enabled
                      ? "text-emerald-50/80 hover:bg-white/10 hover:text-white"
                      : "cursor-not-allowed text-emerald-50/30"
                }`}
              >
                <item.icon className="h-5 w-5" />
                {item.label}
              </button>
            ))}
          </nav>

          <div className="mt-10 rounded-3xl border border-white/10 bg-white/5 p-5 text-sm text-emerald-50/75">
            <div className="font-semibold text-white">Quyền hiện tại</div>
            <div className="mt-3 space-y-2">
              <div>Thông tin nhà hàng: {profileAccess ? "Có" : "Không"}</div>
              <div>Quản lý menu: {menuAccess ? "Có" : "Không"}</div>
              <div>Quản lý booking: {bookingAccess ? "Có" : "Không"}</div>
              <div>Quản lý bàn: {tableAccess ? "Có" : "Không"}</div>
              <div>Quản lý order: {orderAccess ? "Có" : "Không"}</div>
              <div>Quản lý thanh toán: {paymentAccess ? "Có" : "Không"}</div>
              <div>Quản lý nhân sự: {isSuperAdmin ? "Có" : "Không"}</div>
            </div>
          </div>

          <button
            type="button"
            onClick={handleLogout}
            className="mt-8 flex w-full items-center justify-center gap-2 rounded-2xl border border-white/15 px-4 py-3 text-sm font-semibold text-white transition hover:bg-white/10"
          >
            <ArrowRightOnRectangleIcon className="h-5 w-5" />
            Đăng xuất
          </button>
        </aside>

        <main className="px-6 py-8 md:px-10">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <div className="text-xs font-semibold uppercase tracking-[0.3em] text-stone-500">
                Internal Operations
              </div>
              <h2 className="mt-2 text-3xl font-semibold text-stone-900">
                {activeSection === "overview" && "Bảng điều hành"}
                {activeSection === "profile" && "Thông tin nhà hàng"}
                {activeSection === "menu" && "Quản lý menu"}
                {activeSection === "bookings" && "Quản lý đặt bàn"}
                {activeSection === "tables" && "Quản lý bàn ăn"}
                {activeSection === "operations" && "Vận hành phục vụ"}
                {activeSection === "payments" && "Thanh toán và hóa đơn"}
                {activeSection === "team" && "Quản lý nhân sự nội bộ"}
              </h2>
            </div>
            <button
              type="button"
              onClick={() => navigate(GUEST_HOME_PATH)}
              className="inline-flex items-center gap-2 rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm font-semibold text-stone-700 shadow-sm transition hover:border-stone-400 hover:text-stone-900"
            >
              <HomeModernIcon className="h-5 w-5" />
              Xem trang đặt bàn công khai
            </button>
          </div>

          {error && (
            <div className="mt-6 rounded-2xl border border-rose-200 bg-rose-50 px-5 py-4 text-sm text-rose-700">
              {error}
            </div>
          )}

          {sectionLoading && (
            <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-800">
              Đang đồng bộ dữ liệu...
            </div>
          )}

          {activeSection === "overview" && (
            <section className="mt-8 space-y-6">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <div className="text-sm text-stone-500">Tổng booking</div>
                  <div className="mt-3 text-4xl font-semibold text-stone-900">
                    {summary?.bookings?.total ?? 0}
                  </div>
                </div>
                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <div className="text-sm text-stone-500">Chờ xác nhận</div>
                  <div className="mt-3 text-4xl font-semibold text-amber-700">
                    {summary?.bookings?.pending ?? 0}
                  </div>
                </div>
                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <div className="text-sm text-stone-500">Bàn khả dụng</div>
                  <div className="mt-3 text-4xl font-semibold text-emerald-700">
                    {summary?.tables?.available ?? 0}
                  </div>
                </div>
                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <div className="text-sm text-stone-500">Bàn đang phục vụ</div>
                  <div className="mt-3 text-4xl font-semibold text-amber-700">
                    {summary?.tables?.busy ?? 0}
                  </div>
                </div>
                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <div className="text-sm text-stone-500">Bàn bảo trì</div>
                  <div className="mt-3 text-4xl font-semibold text-rose-700">
                    {summary?.tables?.maintenance ?? 0}
                  </div>
                </div>
              </div>

              <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-stone-900">Vận hành hiện tại</h3>
                    <StatusBadge tone="success">
                      {isSuperAdmin ? "Toàn quyền" : "Theo phân quyền"}
                    </StatusBadge>
                  </div>
                  <div className="mt-5 space-y-4 text-sm text-stone-600">
                    <div className="rounded-2xl bg-stone-50 p-4">
                      Guest booking đang mở công khai, không cần đăng nhập.
                    </div>
                    <div className="rounded-2xl bg-stone-50 p-4">
                      Portal nội bộ hiện đã có nền role/permission để mở rộng sang waiter, cashier và các module vận hành.
                    </div>
                    <div className="rounded-2xl bg-stone-50 p-4">
                      Các flow user thường và UI ngoài scope đã được dọn để phạm vi dự án rõ hơn.
                    </div>
                  </div>
                </div>

                <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                  <h3 className="text-lg font-semibold text-stone-900">Tiến độ quyền</h3>
                  <div className="mt-5 space-y-3">
                    <div className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm">
                      <span>Quản lý booking</span>
                      {bookingAccess ? <CheckCircleIcon className="h-5 w-5 text-emerald-600" /> : <XCircleIcon className="h-5 w-5 text-stone-400" />}
                    </div>
                    <div className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm">
                      <span>Quản lý bàn</span>
                      {tableAccess ? <CheckCircleIcon className="h-5 w-5 text-emerald-600" /> : <XCircleIcon className="h-5 w-5 text-stone-400" />}
                    </div>
                    <div className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm">
                      <span>Quản lý nhân sự nội bộ</span>
                      {isSuperAdmin ? <CheckCircleIcon className="h-5 w-5 text-emerald-600" /> : <XCircleIcon className="h-5 w-5 text-stone-400" />}
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}

          {activeSection === "profile" && (
            <section className="mt-8">
              {!profileAccess ? (
                <div className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
                  Tài khoản này chưa được cấp quyền quản lý thông tin nhà hàng.
                </div>
              ) : (
                <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
                  <form
                    onSubmit={submitProfileForm}
                    className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                  >
                    <h3 className="text-lg font-semibold text-stone-900">Hồ sơ nhà hàng</h3>
                    <div className="mt-5 grid gap-4">
                      <input
                        name="name"
                        value={profileForm.name}
                        onChange={handleProfileFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        placeholder="Tên nhà hàng"
                      />
                      <input
                        name="address"
                        value={profileForm.address}
                        onChange={handleProfileFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        placeholder="Địa chỉ"
                      />
                      <div className="grid gap-4 md:grid-cols-2">
                        <input
                          name="phone_number"
                          value={profileForm.phone_number}
                          onChange={handleProfileFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                          placeholder="Số điện thoại"
                        />
                        <input
                          name="email"
                          value={profileForm.email}
                          onChange={handleProfileFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                          placeholder="Email"
                        />
                      </div>
                      <div className="grid gap-4 md:grid-cols-2">
                        <input
                          type="time"
                          name="opening_time"
                          value={profileForm.opening_time}
                          onChange={handleProfileFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        />
                        <input
                          type="time"
                          name="closing_time"
                          value={profileForm.closing_time}
                          onChange={handleProfileFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        />
                      </div>
                      <div className="grid gap-4 md:grid-cols-2">
                        <input
                          name="price_range_min"
                          value={profileForm.price_range_min}
                          onChange={handleProfileFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                          placeholder="Giá thấp nhất"
                        />
                        <input
                          name="price_range_max"
                          value={profileForm.price_range_max}
                          onChange={handleProfileFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                          placeholder="Giá cao nhất"
                        />
                      </div>
                      <input
                        name="website"
                        value={profileForm.website}
                        onChange={handleProfileFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        placeholder="Website"
                      />
                      <textarea
                        name="description"
                        value={profileForm.description}
                        onChange={handleProfileFormChange}
                        rows={4}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        placeholder="Mô tả nhà hàng"
                      />
                      <textarea
                        name="ai_greeting"
                        value={profileForm.ai_greeting}
                        onChange={handleProfileFormChange}
                        rows={4}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        placeholder="Thông điệp AI mặc định"
                      />
                    </div>
                    <button
                      type="submit"
                      className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#22453c]"
                    >
                      Lưu thông tin nhà hàng
                    </button>
                  </form>

                  <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-stone-900">Snapshot cho AI</h3>
                      <StatusBadge tone="success">DB-backed</StatusBadge>
                    </div>
                    <div className="mt-5 grid gap-4 text-sm text-stone-700 md:grid-cols-2">
                      <div className="rounded-2xl bg-stone-50 p-4">
                        <div className="font-semibold text-stone-900">Tên</div>
                        <div className="mt-2">{restaurantProfile?.name || "Chưa cập nhật"}</div>
                      </div>
                      <div className="rounded-2xl bg-stone-50 p-4">
                        <div className="font-semibold text-stone-900">Giờ mở cửa</div>
                        <div className="mt-2">
                          {restaurantProfile?.opening_time || "--:--"} - {restaurantProfile?.closing_time || "--:--"}
                        </div>
                      </div>
                      <div className="rounded-2xl bg-stone-50 p-4">
                        <div className="font-semibold text-stone-900">Liên hệ</div>
                        <div className="mt-2">{restaurantProfile?.phone_number || "Chưa cập nhật"}</div>
                        <div>{restaurantProfile?.email || "Chưa cập nhật"}</div>
                      </div>
                      <div className="rounded-2xl bg-stone-50 p-4">
                        <div className="font-semibold text-stone-900">Khoảng giá</div>
                        <div className="mt-2">
                          {restaurantProfile?.price_range_min ?? "--"} - {restaurantProfile?.price_range_max ?? "--"}
                        </div>
                      </div>
                    </div>
                    <div className="mt-4 rounded-2xl bg-stone-50 p-4 text-sm text-stone-700">
                      <div className="font-semibold text-stone-900">Địa chỉ</div>
                      <div className="mt-2">{restaurantProfile?.address || "Chưa cập nhật"}</div>
                    </div>
                    <div className="mt-4 rounded-2xl bg-stone-50 p-4 text-sm text-stone-700">
                      <div className="font-semibold text-stone-900">Mô tả</div>
                      <div className="mt-2 whitespace-pre-wrap">
                        {restaurantProfile?.description || "Chưa cập nhật"}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </section>
          )}

          {activeSection === "menu" && (
            <section className="mt-8">
              {!menuAccess && !orderAccess ? (
                <div className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
                  Tài khoản này chưa được cấp quyền truy cập menu.
                </div>
              ) : (
                <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
                  <div className="space-y-6">
                    {menuAccess && (
                      <>
                        <form
                          onSubmit={submitCategoryForm}
                          className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                        >
                          <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-stone-900">
                              {editingCategoryId ? "Cập nhật danh mục" : "Danh mục menu"}
                            </h3>
                            {editingCategoryId && (
                              <button
                                type="button"
                                onClick={resetCategoryForm}
                                className="text-sm font-medium text-stone-500 transition hover:text-stone-900"
                              >
                                Hủy
                              </button>
                            )}
                          </div>
                          <div className="mt-5 grid gap-4">
                            <input
                              name="name"
                              value={categoryForm.name}
                              onChange={handleCategoryFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Tên danh mục"
                            />
                            <input
                              type="number"
                              name="display_order"
                              value={categoryForm.display_order}
                              onChange={handleCategoryFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Thứ tự hiển thị"
                            />
                            <textarea
                              name="description"
                              value={categoryForm.description}
                              onChange={handleCategoryFormChange}
                              rows={3}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Mô tả"
                            />
                            <input
                              name="default_image_url"
                              value={categoryForm.default_image_url}
                              onChange={handleCategoryFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="URL ảnh mặc định"
                            />
                            <input
                              name="default_image_alt_text"
                              value={categoryForm.default_image_alt_text}
                              onChange={handleCategoryFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Alt text ảnh mặc định"
                            />
                            <label className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-700">
                              <span>Đang hoạt động</span>
                              <input
                                type="checkbox"
                                name="is_active"
                                checked={categoryForm.is_active}
                                onChange={handleCategoryFormChange}
                                className="h-4 w-4"
                              />
                            </label>
                          </div>
                          <button
                            type="submit"
                            className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#22453c]"
                          >
                            {editingCategoryId ? "Lưu danh mục" : "Tạo danh mục"}
                          </button>
                        </form>

                        <form
                          onSubmit={submitMenuItemForm}
                          className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                        >
                          <div className="flex items-center justify-between">
                            <h3 className="text-lg font-semibold text-stone-900">
                              {editingMenuItemId ? "Cập nhật món" : "Món ăn"}
                            </h3>
                            {editingMenuItemId && (
                              <button
                                type="button"
                                onClick={resetMenuItemForm}
                                className="text-sm font-medium text-stone-500 transition hover:text-stone-900"
                              >
                                Hủy
                              </button>
                            )}
                          </div>
                          <div className="mt-5 grid gap-4">
                            <select
                              name="category"
                              value={itemForm.category}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            >
                              <option value="">Chọn danh mục</option>
                              {menuCategories.map((category) => (
                                <option key={category.id} value={category.id}>
                                  {category.name}
                                </option>
                              ))}
                            </select>
                            <input
                              name="name"
                              value={itemForm.name}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Tên món"
                            />
                            <input
                              name="price"
                              value={itemForm.price}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Giá"
                            />
                            <input
                              name="image_url"
                              value={itemForm.image_url}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="URL ảnh món"
                            />
                            <input
                              name="image_alt_text"
                              value={itemForm.image_alt_text}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Alt text ảnh món"
                            />
                            <select
                              name="status"
                              value={itemForm.status}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            >
                              <option value="ACTIVE">Đang bán</option>
                              <option value="INACTIVE">Tạm ẩn</option>
                              <option value="OUT_OF_STOCK">Hết món</option>
                            </select>
                            <select
                              name="spicy_level"
                              value={itemForm.spicy_level}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            >
                              <option value="NONE">Không cay</option>
                              <option value="MILD">Ít cay</option>
                              <option value="MEDIUM">Cay vừa</option>
                              <option value="HOT">Cay nhiều</option>
                            </select>
                            <input
                              name="preparation_time_minutes"
                              value={itemForm.preparation_time_minutes}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Thời gian chuẩn bị (phút)"
                            />
                            <div className="grid gap-4 sm:grid-cols-2">
                              <input
                                type="time"
                                name="serving_start_time"
                                value={itemForm.serving_start_time}
                                onChange={handleItemFormChange}
                                className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              />
                              <input
                                type="time"
                                name="serving_end_time"
                                value={itemForm.serving_end_time}
                                onChange={handleItemFormChange}
                                className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              />
                            </div>
                            <textarea
                              name="description"
                              value={itemForm.description}
                              onChange={handleItemFormChange}
                              rows={3}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Mô tả món"
                            />
                            <input
                              name="tags_input"
                              value={itemForm.tags_input}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Tags, cách nhau bằng dấu phẩy"
                            />
                            <input
                              name="dietary_labels_input"
                              value={itemForm.dietary_labels_input}
                              onChange={handleItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Dietary labels, ví dụ: halal, gluten-free"
                            />
                            <select
                              multiple
                              name="suggested_pairings"
                              value={itemForm.suggested_pairings}
                              onChange={handleItemFormChange}
                              className="min-h-[150px] rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            >
                              {menuItems
                                .filter((item) => item.id !== editingMenuItemId)
                                .map((item) => (
                                  <option key={item.id} value={item.id}>
                                    {item.name}
                                  </option>
                                ))}
                            </select>
                            <label className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-700">
                              <span>Món gợi ý</span>
                              <input
                                type="checkbox"
                                name="is_recommended"
                                checked={itemForm.is_recommended}
                                onChange={handleItemFormChange}
                                className="h-4 w-4"
                              />
                            </label>
                            <label className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-700">
                              <span>Món chay</span>
                              <input
                                type="checkbox"
                                name="is_vegetarian"
                                checked={itemForm.is_vegetarian}
                                onChange={handleItemFormChange}
                                className="h-4 w-4"
                              />
                            </label>
                            <label className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-700">
                              <span>Best seller</span>
                              <input
                                type="checkbox"
                                name="is_best_seller"
                                checked={itemForm.is_best_seller}
                                onChange={handleItemFormChange}
                                className="h-4 w-4"
                              />
                            </label>
                            <label className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-700">
                              <span>Phù hợp trẻ em</span>
                              <input
                                type="checkbox"
                                name="is_kid_friendly"
                                checked={itemForm.is_kid_friendly}
                                onChange={handleItemFormChange}
                                className="h-4 w-4"
                              />
                            </label>
                            <label className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-700">
                              <span>Ảnh minh họa</span>
                              <input
                                type="checkbox"
                                name="is_illustration"
                                checked={itemForm.is_illustration}
                                onChange={handleItemFormChange}
                                className="h-4 w-4"
                              />
                            </label>
                          </div>
                          <button
                            type="submit"
                            className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#22453c]"
                          >
                            {editingMenuItemId ? "Lưu món" : "Tạo món"}
                          </button>
                        </form>
                      </>
                    )}
                  </div>

                  <div className="space-y-6">
                    <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-stone-900">Danh mục hiện có</h3>
                      <div className="mt-5 space-y-3">
                        {menuCategories.map((category) => (
                          <div
                            key={category.id}
                            className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-4 text-sm"
                          >
                            <div>
                              <div className="font-semibold text-stone-900">{category.name}</div>
                              <div className="mt-1 text-stone-600">
                                Thứ tự {category.display_order} · {category.is_active ? "Hiển thị" : "Ẩn"}
                              </div>
                              {category.default_image_url && (
                                <div className="mt-1 text-xs text-stone-500">Đã có ảnh mặc định</div>
                              )}
                            </div>
                            {menuAccess && (
                              <div className="flex gap-2">
                                <button
                                  type="button"
                                  onClick={() => editCategory(category)}
                                  className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700"
                                >
                                  Sửa
                                </button>
                                <button
                                  type="button"
                                  onClick={() => removeCategory(category.id)}
                                  className="rounded-2xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white"
                                >
                                  Xóa
                                </button>
                              </div>
                            )}
                          </div>
                        ))}
                        {menuCategories.length === 0 && (
                          <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-8 text-center text-sm text-stone-500">
                            Chưa có danh mục menu.
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-stone-900">Món ăn hiện có</h3>
                      <div className="mt-5 space-y-4">
                        {menuItems.map((item) => (
                          <div
                            key={item.id}
                            className="rounded-2xl bg-stone-50 p-4"
                          >
                            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                              <div>
                                <div className="flex flex-wrap items-center gap-2">
                                  <div className="font-semibold text-stone-900">{item.name}</div>
                                  <StatusBadge tone={item.status === "ACTIVE" ? "success" : item.status === "OUT_OF_STOCK" ? "danger" : "warning"}>
                                    {item.status}
                                  </StatusBadge>
                                  {item.is_recommended && <StatusBadge tone="success">Gợi ý</StatusBadge>}
                                  {item.is_best_seller && <StatusBadge tone="success">Best seller</StatusBadge>}
                                  {item.is_vegetarian && <StatusBadge>Chay</StatusBadge>}
                                  {item.is_kid_friendly && <StatusBadge>Trẻ em</StatusBadge>}
                                  {item.is_illustration && <StatusBadge tone="warning">Ảnh minh họa</StatusBadge>}
                                </div>
                                <div className="mt-2 text-sm text-stone-600">
                                  {item.category_name || "Chưa có danh mục"} · {item.price}
                                </div>
                                <div className="mt-2 flex flex-wrap gap-2 text-xs text-stone-500">
                                  {item.spicy_level && <span>Cay: {item.spicy_level}</span>}
                                  {item.serving_start_time && <span>Từ: {item.serving_start_time}</span>}
                                  {item.serving_end_time && <span>Đến: {item.serving_end_time}</span>}
                                  {item.suggested_pairing_items?.length ? (
                                    <span>Pairing: {item.suggested_pairing_items.map((pairing) => pairing.name).join(", ")}</span>
                                  ) : null}
                                </div>
                                {item.tags?.length ? (
                                  <div className="mt-2 flex flex-wrap gap-2">
                                    {item.tags.map((tag) => (
                                      <span
                                        key={`${item.id}-${tag}`}
                                        className="rounded-full border border-stone-300 bg-white px-2 py-1 text-[11px] text-stone-600"
                                      >
                                        {tag}
                                      </span>
                                    ))}
                                  </div>
                                ) : null}
                                {item.description && (
                                  <div className="mt-2 text-sm text-stone-600">{item.description}</div>
                                )}
                              </div>
                              {menuAccess && (
                                <div className="flex gap-2">
                                  <button
                                    type="button"
                                    onClick={() => editMenuItem(item)}
                                    className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700"
                                  >
                                    Sửa
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => removeMenuItem(item.id)}
                                    className="rounded-2xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white"
                                  >
                                    Xóa
                                  </button>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                        {menuItems.length === 0 && (
                          <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-8 text-center text-sm text-stone-500">
                            Chưa có món nào trong menu.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </section>
          )}

          {activeSection === "bookings" && (
            <section className="mt-8 space-y-6">
              {!bookingAccess ? (
                <div className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
                  SUPER_ADMIN chưa cấp quyền quản lý booking cho tài khoản này.
                </div>
              ) : (
                <>
                  <form
                    onSubmit={handleBookingSearch}
                    className="grid gap-4 rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm md:grid-cols-[1fr_200px_160px]"
                  >
                    <input
                      type="text"
                      name="query"
                      value={bookingFilters.query}
                      onChange={handleBookingFilterChange}
                      placeholder="Tìm theo mã, tên, email, số điện thoại"
                      className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm outline-none focus:border-emerald-500 focus:bg-white"
                    />
                    <select
                      name="status"
                      value={bookingFilters.status}
                      onChange={handleBookingFilterChange}
                      className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm outline-none focus:border-emerald-500 focus:bg-white"
                    >
                      <option value="">Tất cả trạng thái</option>
                      <option value="PENDING">Chờ xác nhận</option>
                      <option value="CONFIRMED">Đã xác nhận</option>
                      <option value="CANCELLED">Đã hủy</option>
                      <option value="COMPLETED">Hoàn thành</option>
                      <option value="NO_SHOW">Không đến</option>
                    </select>
                    <button
                      type="submit"
                      className="rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#22453c]"
                    >
                      Lọc booking
                    </button>
                  </form>

                  <div className="space-y-4">
                    {bookings.map((booking) => (
                      <div
                        key={booking.id}
                        className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                      >
                        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-3">
                              <h3 className="text-lg font-semibold text-stone-900">
                                {booking.guest_name || "Khách chưa cung cấp tên"}
                              </h3>
                              <StatusBadge
                                tone={
                                  booking.status === "CONFIRMED"
                                    ? "success"
                                    : booking.status === "PENDING"
                                      ? "warning"
                                      : booking.status === "CANCELLED"
                                        ? "danger"
                                        : "default"
                                }
                              >
                                {booking.status_label}
                              </StatusBadge>
                              <StatusBadge>{booking.code}</StatusBadge>
                            </div>

                            <div className="mt-3 grid gap-2 text-sm text-stone-600 md:grid-cols-2 xl:grid-cols-4">
                              <div>{booking.guest_email}</div>
                              <div>{booking.guest_phone}</div>
                              <div>
                                {booking.booking_date} lúc {booking.booking_time?.slice(0, 5)}
                              </div>
                              <div>
                                Bàn #{booking.table_id} · {booking.table_type_label} · Tầng {booking.table_floor}
                              </div>
                            </div>

                            {booking.notes && (
                              <div className="mt-4 rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-600">
                                {booking.notes}
                              </div>
                            )}
                          </div>

                          <div className="flex flex-wrap gap-2">
                            {booking.status === "PENDING" && (
                              <>
                                <button
                                  type="button"
                                  onClick={() => handleBookingAction(booking.id, "CONFIRMED")}
                                  className="rounded-2xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
                                >
                                  Xác nhận
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleBookingAction(booking.id, "CANCELLED")}
                                  className="rounded-2xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700"
                                >
                                  Hủy
                                </button>
                              </>
                            )}

                            {booking.status === "CONFIRMED" && (
                              <>
                                <button
                                  type="button"
                                  onClick={() => handleBookingAction(booking.id, "COMPLETED")}
                                  className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                                >
                                  Hoàn thành
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleBookingAction(booking.id, "NO_SHOW")}
                                  className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                                >
                                  Không đến
                                </button>
                                <button
                                  type="button"
                                  onClick={() => handleBookingAction(booking.id, "CANCELLED")}
                                  className="rounded-2xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700"
                                >
                                  Hủy
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}

                    {bookings.length === 0 && (
                      <div className="rounded-[1.75rem] border border-dashed border-stone-300 bg-white p-10 text-center text-sm text-stone-500">
                        Chưa có booking nào khớp bộ lọc hiện tại.
                      </div>
                    )}
                  </div>
                </>
              )}
            </section>
          )}

          {activeSection === "operations" && (
            <section className="mt-8">
              {!orderAccess && !tableAccess && !paymentAccess ? (
                <div className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
                  Tài khoản này chưa được cấp quyền vận hành phục vụ.
                </div>
              ) : (
                <div className="grid gap-6 xl:grid-cols-[420px_1fr]">
                  <div className="space-y-6">
                    {tableAccess && (
                      <form
                        onSubmit={submitSessionForm}
                        className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                      >
                        <h3 className="text-lg font-semibold text-stone-900">Mở phiên phục vụ</h3>
                        <div className="mt-5 grid gap-4">
                          <input
                            name="table_ids"
                            value={sessionForm.table_ids}
                            onChange={handleSessionFormChange}
                            className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            placeholder="Bàn, ví dụ: 1,2"
                          />
                          <input
                            name="guest_name"
                            value={sessionForm.guest_name}
                            onChange={handleSessionFormChange}
                            className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            placeholder="Tên khách"
                          />
                          <input
                            name="guest_phone"
                            value={sessionForm.guest_phone}
                            onChange={handleSessionFormChange}
                            className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            placeholder="Số điện thoại"
                          />
                          <div className="grid gap-4 md:grid-cols-2">
                            <input
                              type="number"
                              min="1"
                              name="guest_count"
                              value={sessionForm.guest_count}
                              onChange={handleSessionFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Số khách"
                            />
                            <input
                              type="number"
                              min="1"
                              name="booking_id"
                              value={sessionForm.booking_id}
                              onChange={handleSessionFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Booking ID"
                            />
                          </div>
                          <textarea
                            name="notes"
                            value={sessionForm.notes}
                            onChange={handleSessionFormChange}
                            rows={3}
                            className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            placeholder="Ghi chú"
                          />
                        </div>
                        <button
                          type="submit"
                          className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white"
                        >
                          Mở phiên
                        </button>
                      </form>
                    )}

                    {orderAccess && (
                      <>
                        <form
                          onSubmit={submitOrderForm}
                          className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                        >
                          <h3 className="text-lg font-semibold text-stone-900">Tạo order</h3>
                          <div className="mt-5 grid gap-4">
                            <input
                              type="number"
                              min="1"
                              name="table_session_id"
                              value={orderForm.table_session_id}
                              onChange={handleOrderFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Session ID"
                            />
                            <textarea
                              name="notes"
                              value={orderForm.notes}
                              onChange={handleOrderFormChange}
                              rows={3}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Ghi chú order"
                            />
                          </div>
                          <button type="submit" className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white">
                            Tạo order
                          </button>
                        </form>

                        <form
                          onSubmit={submitOrderItemForm}
                          className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                        >
                          <h3 className="text-lg font-semibold text-stone-900">Thêm món vào order</h3>
                          <div className="mt-5 grid gap-4">
                            <select
                              name="order_id"
                              value={orderItemForm.order_id}
                              onChange={handleOrderItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            >
                              <option value="">Chọn order</option>
                              {flattenedOrders.map((order) => (
                                <option key={order.id} value={order.id}>
                                  #{order.id} · {order.code} · Session {order.table_session_id}
                                </option>
                              ))}
                            </select>
                            <select
                              name="menu_item_id"
                              value={orderItemForm.menu_item_id}
                              onChange={handleOrderItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            >
                              <option value="">Chọn món</option>
                              {menuItems
                                .filter((item) => item.status === "ACTIVE")
                                .map((item) => (
                                  <option key={item.id} value={item.id}>
                                    {item.name} · {item.price}
                                  </option>
                                ))}
                            </select>
                            <input
                              type="number"
                              min="1"
                              name="quantity"
                              value={orderItemForm.quantity}
                              onChange={handleOrderItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Số lượng"
                            />
                            <input
                              name="note"
                              value={orderItemForm.note}
                              onChange={handleOrderItemFormChange}
                              className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                              placeholder="Ghi chú món"
                            />
                          </div>
                          <button type="submit" className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white">
                            Thêm món
                          </button>
                        </form>

                        <form
                          onSubmit={submitSplitItemForm}
                          className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                        >
                          <h3 className="text-lg font-semibold text-stone-900">Tách món</h3>
                          <div className="mt-5 grid gap-4">
                            <input type="number" min="1" name="order_id" value={splitItemForm.order_id} onChange={handleSplitItemFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Order ID nguồn" />
                            <input type="number" min="1" name="order_item_id" value={splitItemForm.order_item_id} onChange={handleSplitItemFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Order item ID" />
                            <input type="number" min="1" name="quantity" value={splitItemForm.quantity} onChange={handleSplitItemFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Số lượng tách" />
                            <input type="number" min="1" name="target_order_id" value={splitItemForm.target_order_id} onChange={handleSplitItemFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Order ID đích (để trống nếu tạo mới)" />
                          </div>
                          <button type="submit" className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white">
                            Tách món
                          </button>
                        </form>

                        <form
                          onSubmit={submitMergeOrdersForm}
                          className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                        >
                          <h3 className="text-lg font-semibold text-stone-900">Ghép order</h3>
                          <div className="mt-5 grid gap-4">
                            <input type="number" min="1" name="source_order_id" value={mergeOrdersForm.source_order_id} onChange={handleMergeOrdersFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Order nguồn" />
                            <input type="number" min="1" name="target_order_id" value={mergeOrdersForm.target_order_id} onChange={handleMergeOrdersFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Order đích" />
                          </div>
                          <button type="submit" className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white">
                            Ghép order
                          </button>
                        </form>
                      </>
                    )}

                    {tableAccess && (
                      <>
                        <form
                          onSubmit={submitMergeTableForm}
                          className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                        >
                          <h3 className="text-lg font-semibold text-stone-900">Gộp bàn</h3>
                          <div className="mt-5 grid gap-4">
                            <input type="number" min="1" name="session_id" value={mergeTableForm.session_id} onChange={handleMergeTableFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Session ID" />
                            <input type="number" min="1" name="table_id" value={mergeTableForm.table_id} onChange={handleMergeTableFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Bàn cần gộp" />
                          </div>
                          <button type="submit" className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white">
                            Gộp bàn
                          </button>
                        </form>

                        <form
                          onSubmit={submitMoveTableForm}
                          className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                        >
                          <h3 className="text-lg font-semibold text-stone-900">Chuyển bàn</h3>
                          <div className="mt-5 grid gap-4">
                            <input type="number" min="1" name="session_id" value={moveTableForm.session_id} onChange={handleMoveTableFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Session ID" />
                            <input type="number" min="1" name="from_table_id" value={moveTableForm.from_table_id} onChange={handleMoveTableFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Bàn nguồn" />
                            <input type="number" min="1" name="to_table_id" value={moveTableForm.to_table_id} onChange={handleMoveTableFormChange} className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm" placeholder="Bàn đích" />
                          </div>
                          <button type="submit" className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white">
                            Chuyển bàn
                          </button>
                        </form>
                      </>
                    )}
                  </div>

                  <div className="space-y-4">
                    {sessions.map((sessionItem) => (
                      <div
                        key={sessionItem.id}
                        className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                      >
                        <div className="flex flex-col gap-4 xl:flex-row xl:items-start xl:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-3">
                              <h3 className="text-lg font-semibold text-stone-900">
                                Session #{sessionItem.id} · {sessionItem.code}
                              </h3>
                              <StatusBadge tone={sessionItem.status === "CLOSED" ? "default" : "success"}>
                                {sessionItem.status}
                              </StatusBadge>
                            </div>
                            <div className="mt-3 grid gap-2 text-sm text-stone-600 md:grid-cols-2">
                              <div>{sessionItem.guest_name || "Khách lẻ"}</div>
                              <div>{sessionItem.guest_phone || "Chưa có SĐT"}</div>
                              <div>{sessionItem.guest_count} khách</div>
                              <div>
                                Bàn: {(sessionItem.session_tables || [])
                                  .filter((tableItem) => tableItem.is_active)
                                  .map((tableItem) => `#${tableItem.table}`)
                                  .join(", ") || "Chưa gán"}
                              </div>
                            </div>
                            {sessionItem.notes && (
                              <div className="mt-4 rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-600">
                                {sessionItem.notes}
                              </div>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {orderAccess && sessionItem.status !== "CLOSED" && (
                              <button
                                type="button"
                                onClick={() => handleQuickCreateOrder(sessionItem.id)}
                                className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700"
                              >
                                Tạo order
                              </button>
                            )}
                            {paymentAccess && sessionItem.status !== "CLOSED" && (
                              <button
                                type="button"
                                onClick={() => handleQuickCheckout(sessionItem.id)}
                                className="rounded-2xl bg-[#16322c] px-4 py-2 text-sm font-semibold text-white"
                              >
                                Checkout
                              </button>
                            )}
                          </div>
                        </div>

                        <div className="mt-5 space-y-4">
                          {(sessionItem.orders || []).map((order) => (
                            <div key={order.id} className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
                              <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                                <div>
                                  <div className="flex flex-wrap items-center gap-2">
                                    <div className="font-semibold text-stone-900">
                                      Order #{order.id} · {order.code}
                                    </div>
                                    <StatusBadge tone={order.status === "OPEN" ? "warning" : order.status === "SENT_TO_KITCHEN" ? "success" : "default"}>
                                      {order.status}
                                    </StatusBadge>
                                  </div>
                                  <div className="mt-2 text-sm text-stone-600">
                                    Tạm tính: {order.subtotal_amount}
                                  </div>
                                  {order.notes && (
                                    <div className="mt-2 text-sm text-stone-600">{order.notes}</div>
                                  )}
                                </div>
                                {orderAccess && order.status !== "COMPLETED" && order.status !== "CANCELLED" && (
                                  <button
                                    type="button"
                                    onClick={() => handleSendOrderToKitchen(order.id)}
                                    className="rounded-2xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white"
                                  >
                                    Gửi bếp
                                  </button>
                                )}
                              </div>

                              <div className="mt-4 space-y-3">
                                {(order.items || []).map((item) => (
                                  <div key={item.id} className="flex flex-col gap-3 rounded-2xl bg-white px-4 py-4 text-sm md:flex-row md:items-start md:justify-between">
                                    <div>
                                      <div className="font-semibold text-stone-900">
                                        #{item.id} · {item.item_name} x{item.quantity}
                                      </div>
                                      <div className="mt-1 text-stone-600">
                                        Đơn giá {item.unit_price} · Thành tiền {item.line_total}
                                      </div>
                                      <div className="mt-1 text-stone-600">
                                        {item.kitchen_status}
                                      </div>
                                      {item.note && <div className="mt-1 text-stone-600">{item.note}</div>}
                                    </div>
                                    {orderAccess && (
                                      <div className="flex gap-2">
                                        <button
                                          type="button"
                                          onClick={() => handleEditOrderItem(item)}
                                          className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700"
                                        >
                                          Sửa
                                        </button>
                                        <button
                                          type="button"
                                          onClick={() => handleDeleteOrderItem(item.id)}
                                          className="rounded-2xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white"
                                        >
                                          Xóa
                                        </button>
                                      </div>
                                    )}
                                  </div>
                                ))}
                                {(order.items || []).length === 0 && (
                                  <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-6 text-center text-sm text-stone-500">
                                    Order này chưa có món.
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                          {(sessionItem.orders || []).length === 0 && (
                            <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-8 text-center text-sm text-stone-500">
                              Session này chưa có order.
                            </div>
                          )}
                        </div>
                      </div>
                    ))}

                    {sessions.length === 0 && (
                      <div className="rounded-[1.75rem] border border-dashed border-stone-300 bg-white p-10 text-center text-sm text-stone-500">
                        Chưa có phiên phục vụ nào.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </section>
          )}

          {activeSection === "tables" && (
            <section className="mt-8 grid gap-6 xl:grid-cols-[360px_1fr]">
              {!tableAccess ? (
                <div className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
                  SUPER_ADMIN chưa cấp quyền quản lý bàn cho tài khoản này.
                </div>
              ) : (
                <>
                  <form
                    onSubmit={submitTableForm}
                    className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-stone-900">
                        {editingTableId ? "Cập nhật bàn" : "Thêm bàn mới"}
                      </h3>
                      {editingTableId && (
                        <button
                          type="button"
                          onClick={resetTableForm}
                          className="text-sm font-medium text-stone-500 transition hover:text-stone-900"
                        >
                          Hủy chỉnh sửa
                        </button>
                      )}
                    </div>

                    <div className="mt-5 grid gap-4">
                      <select
                        name="table_type"
                        value={tableForm.table_type}
                        onChange={handleTableFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                      >
                        <option value="INDOOR">Trong nhà</option>
                        <option value="OUTDOOR">Ngoài trời</option>
                        <option value="PRIVATE">Phòng riêng</option>
                        <option value="BAR">Quầy bar</option>
                        <option value="BOOTH">Ghế ngồi</option>
                        <option value="WINDOW">Gần cửa sổ</option>
                      </select>
                      <div className="grid gap-4 sm:grid-cols-2">
                        <input
                          type="number"
                          name="capacity"
                          min="1"
                          max="20"
                          value={tableForm.capacity}
                          onChange={handleTableFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                          placeholder="Sức chứa"
                        />
                        <input
                          type="number"
                          name="floor"
                          min="1"
                          max="2"
                          value={tableForm.floor}
                          onChange={handleTableFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                          placeholder="Tầng"
                        />
                      </div>
                      <select
                        name="status"
                        value={tableForm.status}
                        onChange={handleTableFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                      >
                        <option value="AVAILABLE">Có sẵn</option>
                        <option value="OCCUPIED">Đang sử dụng</option>
                        <option value="RESERVED">Đã đặt</option>
                        <option value="MAINTENANCE">Bảo trì</option>
                      </select>
                      <div className="grid gap-4 sm:grid-cols-2">
                        <input
                          type="number"
                          step="0.01"
                          name="width"
                          value={tableForm.width}
                          onChange={handleTableFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                          placeholder="Chiều rộng (m)"
                        />
                        <input
                          type="number"
                          step="0.01"
                          name="length"
                          value={tableForm.length}
                          onChange={handleTableFormChange}
                          className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                          placeholder="Chiều dài (m)"
                        />
                      </div>
                      <textarea
                        name="notes"
                        value={tableForm.notes}
                        onChange={handleTableFormChange}
                        rows={4}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        placeholder="Ghi chú nội bộ"
                      />
                    </div>

                    <button
                      type="submit"
                      className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#22453c]"
                    >
                      {editingTableId ? "Lưu thay đổi" : "Tạo bàn"}
                    </button>
                  </form>

                  <div className="space-y-4">
                    {tables.map((table) => (
                      <div
                        key={table.id}
                        className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                      >
                        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                          <div>
                            <div className="flex items-center gap-3">
                              <h3 className="text-lg font-semibold text-stone-900">
                                Bàn #{table.id}
                              </h3>
                              <StatusBadge tone={getTableStatusTone(table.status)}>
                                {table.status_label}
                              </StatusBadge>
                            </div>
                            <div className="mt-3 grid gap-2 text-sm text-stone-600 md:grid-cols-3">
                              <div>{table.table_type_label}</div>
                              <div>Sức chứa {table.capacity} khách</div>
                              <div>Tầng {table.floor}</div>
                            </div>
                            {table.notes && (
                              <div className="mt-4 rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-600">
                                {table.notes}
                              </div>
                            )}
                          </div>

                          <div className="flex flex-wrap gap-2">
                            {table.status === "AVAILABLE" && (
                              <button
                                type="button"
                                onClick={() => handleQuickTableStatus(table.id, "RESERVED")}
                                className="rounded-2xl bg-amber-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-amber-700"
                              >
                                Đánh dấu đã đặt
                              </button>
                            )}
                            {table.status !== "AVAILABLE" && table.status !== "MAINTENANCE" && (
                              <button
                                type="button"
                                onClick={() => handleReleaseTable(table.id)}
                                className="rounded-2xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700"
                              >
                                Đánh dấu trống
                              </button>
                            )}
                            {table.status === "MAINTENANCE" ? (
                              <button
                                type="button"
                                onClick={() => handleQuickTableStatus(table.id, "AVAILABLE")}
                                className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                              >
                                Mở lại bàn
                              </button>
                            ) : (
                              <button
                                type="button"
                                onClick={() => handleQuickTableStatus(table.id, "MAINTENANCE")}
                                className="rounded-2xl border border-rose-300 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:border-rose-400 hover:text-rose-900"
                              >
                                Bảo trì
                              </button>
                            )}
                            <button
                              type="button"
                              onClick={() => editTable(table)}
                              className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                            >
                              Sửa
                            </button>
                            <button
                              type="button"
                              onClick={() => removeTable(table.id)}
                              className="rounded-2xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700"
                            >
                              Xóa
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </section>
          )}

          {activeSection === "payments" && (
            <section className="mt-8">
              {!paymentAccess && !reportAccess ? (
                <div className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
                  Tài khoản này chưa được cấp quyền thanh toán hoặc báo cáo.
                </div>
              ) : (
                <div className="grid gap-6 xl:grid-cols-[380px_1fr]">
                  <div className="space-y-6">
                    {paymentAccess && (
                      <form
                        onSubmit={submitCheckoutForm}
                        className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                      >
                        <div className="flex items-center gap-3">
                          <ReceiptPercentIcon className="h-6 w-6 text-[#16322c]" />
                          <h3 className="text-lg font-semibold text-stone-900">Checkout phiên phục vụ</h3>
                        </div>
                        <div className="mt-5 grid gap-4">
                          <input
                            type="number"
                            min="1"
                            name="session_id"
                            value={checkoutForm.session_id}
                            onChange={handleCheckoutFormChange}
                            className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            placeholder="Session ID"
                          />
                          <select
                            name="method"
                            value={checkoutForm.method}
                            onChange={handleCheckoutFormChange}
                            className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                          >
                            <option value="CASH">Tiền mặt</option>
                            <option value="BANK_TRANSFER">Chuyển khoản</option>
                            <option value="CARD">Thẻ</option>
                          </select>
                          <textarea
                            name="note"
                            value={checkoutForm.note}
                            onChange={handleCheckoutFormChange}
                            rows={3}
                            className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                            placeholder="Ghi chú thanh toán"
                          />
                          <label className="flex items-center justify-between rounded-2xl bg-stone-50 px-4 py-3 text-sm text-stone-700">
                            <span>Xuất bill ngay</span>
                            <input
                              type="checkbox"
                              name="issue_invoice"
                              checked={checkoutForm.issue_invoice}
                              onChange={handleCheckoutFormChange}
                              className="h-4 w-4"
                            />
                          </label>
                        </div>
                        <button
                          type="submit"
                          className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white"
                        >
                          Xác nhận thanh toán
                        </button>
                        <div className="mt-4 rounded-2xl bg-stone-50 p-4 text-sm text-stone-600">
                          Phương thức `CARD` sẽ tự cộng phụ phí 3.5% theo backend.
                        </div>
                      </form>
                    )}
                  </div>

                  <div className="space-y-6">
                    <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-stone-900">Lịch sử thanh toán</h3>
                      <div className="mt-5 space-y-3">
                        {payments.map((payment) => (
                          <div key={payment.id} className="rounded-2xl bg-stone-50 p-4">
                            <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                              <div>
                                <div className="flex flex-wrap items-center gap-2">
                                  <div className="font-semibold text-stone-900">
                                    Payment #{payment.id} · {payment.code}
                                  </div>
                                  <StatusBadge tone={payment.status === "PAID" ? "success" : "warning"}>
                                    {payment.status}
                                  </StatusBadge>
                                </div>
                                <div className="mt-2 text-sm text-stone-600">
                                  Session {payment.table_session} · {payment.method}
                                </div>
                                <div className="mt-2 text-sm text-stone-600">
                                  Tạm tính {payment.subtotal_amount} · Phụ phí {payment.surcharge_amount} · Tổng {payment.total_amount}
                                </div>
                              </div>
                              <div className="text-sm text-stone-600">
                                {payment.paid_at || "Chưa thanh toán"}
                              </div>
                            </div>
                          </div>
                        ))}
                        {payments.length === 0 && (
                          <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-8 text-center text-sm text-stone-500">
                            Chưa có giao dịch thanh toán.
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm">
                      <h3 className="text-lg font-semibold text-stone-900">Bill đã xuất</h3>
                      <div className="mt-5 space-y-3">
                        {invoices.map((invoice) => (
                          <div key={invoice.id} className="rounded-2xl bg-stone-50 p-4 text-sm">
                            <div className="flex flex-wrap items-center gap-2">
                              <div className="font-semibold text-stone-900">
                                {invoice.invoice_number}
                              </div>
                              <StatusBadge tone="success">Bill</StatusBadge>
                            </div>
                            <div className="mt-2 text-stone-600">
                              Session {invoice.table_session} · Payment {invoice.payment || "N/A"}
                            </div>
                            <div className="mt-2 text-stone-600">
                              Tổng cộng {invoice.total_amount}
                            </div>
                            <div className="mt-2 text-stone-600">{invoice.issued_at}</div>
                          </div>
                        ))}
                        {invoices.length === 0 && (
                          <div className="rounded-2xl border border-dashed border-stone-300 bg-white px-4 py-8 text-center text-sm text-stone-500">
                            Chưa có bill nào được xuất.
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </section>
          )}

          {activeSection === "team" && (
            <section className="mt-8 grid gap-6 xl:grid-cols-[360px_1fr]">
              {!isSuperAdmin ? (
                <div className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
                  Chỉ SUPER_ADMIN mới được quản lý nhân sự nội bộ.
                </div>
              ) : (
                <>
                  <form
                    onSubmit={submitTeamForm}
                    className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-stone-900">
                        {editingUserId ? "Cập nhật nhân sự" : "Tạo nhân sự mới"}
                      </h3>
                      {editingUserId && (
                        <button
                          type="button"
                          onClick={resetTeamForm}
                          className="text-sm font-medium text-stone-500 transition hover:text-stone-900"
                        >
                          Hủy chỉnh sửa
                        </button>
                      )}
                    </div>

                    <div className="mt-5 grid gap-4">
                      <input
                        type="email"
                        name="email"
                        value={teamForm.email}
                        onChange={handleTeamFormChange}
                        disabled={Boolean(editingUserId)}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm disabled:opacity-60"
                        placeholder="Email nhân sự"
                      />
                      <input
                        type="text"
                        name="full_name"
                        value={teamForm.full_name}
                        onChange={handleTeamFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        placeholder="Họ tên"
                      />
                      <input
                        type="password"
                        name="password"
                        value={teamForm.password}
                        onChange={handleTeamFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        placeholder={editingUserId ? "Đổi mật khẩu nếu cần" : "Mật khẩu tạm"}
                      />
                      <input
                        type="text"
                        name="phone_number"
                        value={teamForm.phone_number}
                        onChange={handleTeamFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                        placeholder="Số điện thoại"
                      />
                      <select
                        name="role"
                        value={teamForm.role}
                        onChange={handleTeamFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                      >
                        {INTERNAL_ROLE_OPTIONS.map((roleOption) => (
                          <option key={roleOption.value} value={roleOption.value}>
                            {roleOption.label}
                          </option>
                        ))}
                      </select>
                      <select
                        name="status"
                        value={teamForm.status}
                        onChange={handleTeamFormChange}
                        className="rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 text-sm"
                      >
                        <option value="ACTIVE">ACTIVE</option>
                        <option value="BLOCKED">BLOCKED</option>
                        <option value="INACTIVE">INACTIVE</option>
                      </select>
                    </div>

                    <div className="mt-6 rounded-3xl bg-stone-50 p-4">
                      <div className="text-sm font-semibold text-stone-900">Quyền thao tác</div>
                      <div className="mt-4 grid gap-3 md:grid-cols-2">
                        {PERMISSION_OPTIONS.map((permission) => (
                          <label
                            key={permission.key}
                            className="flex items-center justify-between rounded-2xl bg-white px-4 py-3 text-sm text-stone-700"
                          >
                            <span>{permission.label}</span>
                            <input
                              type="checkbox"
                              checked={Boolean(teamForm.admin_permissions[permission.key])}
                              onChange={() => handlePermissionToggle(permission.key)}
                              className="h-4 w-4"
                            />
                          </label>
                        ))}
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#22453c]"
                    >
                      {editingUserId ? "Lưu nhân sự" : "Tạo nhân sự"}
                    </button>
                  </form>

                  <div className="space-y-4">
                    {teamUsers.map((user) => (
                      <div
                        key={user.id}
                        className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                      >
                        <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                          <div>
                            <div className="flex flex-wrap items-center gap-3">
                              <h3 className="text-lg font-semibold text-stone-900">
                                {user.full_name || user.email}
                              </h3>
                              <StatusBadge tone={user.role === "SUPER_ADMIN" ? "success" : "default"}>
                                {user.role}
                              </StatusBadge>
                              <StatusBadge>{user.status}</StatusBadge>
                            </div>
                            <div className="mt-3 grid gap-2 text-sm text-stone-600 md:grid-cols-2">
                              <div>{user.email}</div>
                              <div>{user.phone_number || "Chưa có số điện thoại"}</div>
                            </div>
                            <div className="mt-4 flex flex-wrap gap-2">
                              {PERMISSION_OPTIONS.filter(
                                (permission) => user.admin_permissions?.[permission.key]
                              ).map((permission) => (
                                <StatusBadge key={permission.key} tone="success">
                                  {permission.label}
                                </StatusBadge>
                              ))}
                              {!PERMISSION_OPTIONS.some(
                                (permission) => user.admin_permissions?.[permission.key]
                              ) && <StatusBadge>Chưa cấp quyền</StatusBadge>}
                            </div>
                          </div>

                          {user.role !== "SUPER_ADMIN" && (
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={() => editUser(user)}
                                className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                              >
                                Cập nhật
                              </button>
                              <button
                                type="button"
                                onClick={() => removeUser(user.id)}
                                className="rounded-2xl bg-rose-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-rose-700"
                              >
                                Xóa
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </>
              )}
            </section>
          )}
        </main>
      </div>
    </div>
  );
};

export default AdminPortal;
