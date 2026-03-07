import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRightOnRectangleIcon,
  CheckCircleIcon,
  ClipboardDocumentListIcon,
  HomeModernIcon,
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

const EMPTY_TEAM_FORM = {
  email: "",
  full_name: "",
  password: "",
  phone_number: "",
  status: "ACTIVE",
  admin_permissions: {
    manage_bookings: true,
    manage_tables: true,
  },
};


function getErrorMessage(error) {
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
  const [teamForm, setTeamForm] = useState(EMPTY_TEAM_FORM);
  const [editingUserId, setEditingUserId] = useState(null);
  const sessionRef = useRef(null);
  const loadPortalDataRef = useRef(null);
  const queueRealtimeRefreshRef = useRef(null);
  const realtimeRefreshInFlightRef = useRef(false);
  const pendingRealtimeRefreshRef = useRef(false);

  const bookingAccess = session?.admin_permissions?.manage_bookings;
  const tableAccess = session?.admin_permissions?.manage_tables;
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

      if (event.type === "booking.changed" || event.type === "table.changed") {
        queueRealtimeRefresh();
      }
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
    setTeamForm(EMPTY_TEAM_FORM);
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
      status: user.status,
      admin_permissions: {
        manage_bookings: Boolean(user.admin_permissions?.manage_bookings),
        manage_tables: Boolean(user.admin_permissions?.manage_tables),
      },
    });
    setActiveSection("team");
  };

  const removeUser = async (userId) => {
    if (!window.confirm("Xóa tài khoản admin này?")) {
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

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-stone-100">
        <div className="rounded-3xl border border-stone-200 bg-white px-6 py-5 text-sm text-stone-600 shadow-lg">
          Đang tải cổng quản trị...
        </div>
      </div>
    );
  }

  const navigationItems = [
    { id: "overview", label: "Tổng quan", icon: Squares2X2Icon, enabled: true },
    { id: "bookings", label: "Đặt bàn", icon: ClipboardDocumentListIcon, enabled: bookingAccess },
    { id: "tables", label: "Bàn ăn", icon: TableCellsIcon, enabled: tableAccess },
    { id: "team", label: "Quản trị viên", icon: UserGroupIcon, enabled: isSuperAdmin },
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
              <div>Quản lý booking: {bookingAccess ? "Có" : "Không"}</div>
              <div>Quản lý bàn: {tableAccess ? "Có" : "Không"}</div>
              <div>Quản lý admin: {isSuperAdmin ? "Có" : "Không"}</div>
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
                Admin Operations
              </div>
              <h2 className="mt-2 text-3xl font-semibold text-stone-900">
                {activeSection === "overview" && "Bảng điều hành"}
                {activeSection === "bookings" && "Quản lý đặt bàn"}
                {activeSection === "tables" && "Quản lý bàn ăn"}
                {activeSection === "team" && "Quản lý tài khoản admin"}
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
                      Portal admin hiện chỉ tập trung vào booking, bàn ăn và phân quyền admin.
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
                      <span>Quản lý tài khoản admin</span>
                      {isSuperAdmin ? <CheckCircleIcon className="h-5 w-5 text-emerald-600" /> : <XCircleIcon className="h-5 w-5 text-stone-400" />}
                    </div>
                  </div>
                </div>
              </div>
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

          {activeSection === "team" && (
            <section className="mt-8 grid gap-6 xl:grid-cols-[360px_1fr]">
              {!isSuperAdmin ? (
                <div className="rounded-[1.75rem] border border-amber-200 bg-amber-50 p-6 text-sm text-amber-800">
                  Chỉ SUPER_ADMIN mới được quản lý tài khoản admin.
                </div>
              ) : (
                <>
                  <form
                    onSubmit={submitTeamForm}
                    className="rounded-[1.75rem] border border-stone-200 bg-white p-6 shadow-sm"
                  >
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold text-stone-900">
                        {editingUserId ? "Cập nhật admin" : "Tạo admin mới"}
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
                        placeholder="Email admin"
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
                      <div className="text-sm font-semibold text-stone-900">Quyền cho admin</div>
                      <div className="mt-4 space-y-3">
                        <label className="flex items-center justify-between rounded-2xl bg-white px-4 py-3 text-sm text-stone-700">
                          <span>Quản lý booking</span>
                          <input
                            type="checkbox"
                            checked={teamForm.admin_permissions.manage_bookings}
                            onChange={() => handlePermissionToggle("manage_bookings")}
                            className="h-4 w-4"
                          />
                        </label>
                        <label className="flex items-center justify-between rounded-2xl bg-white px-4 py-3 text-sm text-stone-700">
                          <span>Quản lý bàn</span>
                          <input
                            type="checkbox"
                            checked={teamForm.admin_permissions.manage_tables}
                            onChange={() => handlePermissionToggle("manage_tables")}
                            className="h-4 w-4"
                          />
                        </label>
                      </div>
                    </div>

                    <button
                      type="submit"
                      className="mt-5 w-full rounded-2xl bg-[#16322c] px-4 py-3 text-sm font-semibold text-white transition hover:bg-[#22453c]"
                    >
                      {editingUserId ? "Lưu admin" : "Tạo admin"}
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
                              <StatusBadge tone={user.admin_permissions?.manage_bookings ? "success" : "default"}>
                                Booking {user.admin_permissions?.manage_bookings ? "ON" : "OFF"}
                              </StatusBadge>
                              <StatusBadge tone={user.admin_permissions?.manage_tables ? "success" : "default"}>
                                Tables {user.admin_permissions?.manage_tables ? "ON" : "OFF"}
                              </StatusBadge>
                            </div>
                          </div>

                          {user.role === "ADMIN" && (
                            <div className="flex gap-2">
                              <button
                                type="button"
                                onClick={() => editUser(user)}
                                className="rounded-2xl border border-stone-300 px-4 py-2 text-sm font-semibold text-stone-700 transition hover:border-stone-400 hover:text-stone-900"
                              >
                                Sửa
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
