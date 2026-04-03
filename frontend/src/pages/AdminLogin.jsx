import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  LockClosedIcon,
  ShieldCheckIcon,
  UserCircleIcon,
} from "@heroicons/react/24/outline";
import { auth, setAdminAuthTokens } from "../api";
import { ADMIN_PORTAL_PATH, GUEST_HOME_PATH } from "../constants/routes.js";


function getErrorMessage(error) {
  return (
    error?.response?.data?.message ||
    error?.response?.data?.detail ||
    error?.message ||
    "Không thể đăng nhập. Vui lòng thử lại."
  );
}


const AdminLogin = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setIsSubmitting(true);
    setError("");

    try {
      const response = await auth.login(formData);
      const payload = response.data?.data;
      const user = payload?.user;

      if (!payload?.access_token || !payload?.refresh_token || !user?.has_portal_access) {
        throw new Error("Tài khoản này không được phép truy cập cổng quản trị.");
      }

      setAdminAuthTokens({
        accessToken: payload.access_token,
        refreshToken: payload.refresh_token,
      });
      navigate(ADMIN_PORTAL_PATH, { replace: true });
    } catch (submitError) {
      setError(getErrorMessage(submitError));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(176,215,198,0.65),_transparent_38%),linear-gradient(135deg,_#f6f0e5_0%,_#fffaf2_48%,_#f2f6f0_100%)] px-6 py-10">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl items-center justify-center">
        <div className="grid w-full overflow-hidden rounded-[2rem] border border-stone-200 bg-white/90 shadow-[0_32px_120px_rgba(59,52,43,0.12)] backdrop-blur md:grid-cols-[1.15fr_0.85fr]">
          <section className="bg-[#19342e] px-8 py-10 text-white md:px-12 md:py-14">
            <div className="flex items-center gap-3 text-sm uppercase tracking-[0.3em] text-emerald-200/80">
              <ShieldCheckIcon className="h-5 w-5" />
              PSCD Admin Portal
            </div>
            <h1 className="mt-8 max-w-lg text-4xl font-semibold leading-tight md:text-5xl">
              Quản lý vận hành nội bộ nhà hàng tại một nơi.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-7 text-emerald-100/75">
              Hệ thống dùng cho các vai trò nội bộ như admin, waiter, cashier và super admin.
              SUPER_ADMIN giữ quyền cấu hình cao nhất.
            </p>

            <div className="mt-10 grid gap-4">
              <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
                <div className="text-sm font-medium text-emerald-100">SUPER_ADMIN</div>
                <p className="mt-2 text-sm leading-6 text-emerald-50/80">
                  Toàn quyền với dashboard, booking, bàn ăn và quản lý nhân sự nội bộ.
                </p>
              </div>
              <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
                <div className="text-sm font-medium text-emerald-100">INTERNAL ROLES</div>
                <p className="mt-2 text-sm leading-6 text-emerald-50/80">
                  Admin, waiter và cashier thao tác theo phạm vi quyền được cấp.
                </p>
              </div>
            </div>
          </section>

          <section className="px-8 py-10 md:px-12 md:py-14">
            <div className="mx-auto max-w-md">
              <div className="inline-flex items-center rounded-full border border-amber-200 bg-amber-50 px-4 py-2 text-xs font-semibold uppercase tracking-[0.25em] text-amber-700">
                Internal Access
              </div>
              <h2 className="mt-6 text-3xl font-semibold text-stone-900">Đăng nhập quản trị</h2>
              <p className="mt-3 text-sm leading-6 text-stone-500">
                Sử dụng tài khoản nội bộ để vào cổng điều hành.
              </p>

              <form onSubmit={handleSubmit} className="mt-10 space-y-5">
                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-stone-700">Email</span>
                  <div className="flex items-center rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 focus-within:border-emerald-500 focus-within:bg-white">
                    <UserCircleIcon className="mr-3 h-5 w-5 text-stone-400" />
                    <input
                      type="email"
                      name="email"
                      value={formData.email}
                      onChange={handleChange}
                      required
                      className="w-full bg-transparent text-sm text-stone-900 outline-none"
                      placeholder="staff@pscd.com"
                    />
                  </div>
                </label>

                <label className="block">
                  <span className="mb-2 block text-sm font-medium text-stone-700">Mật khẩu</span>
                  <div className="flex items-center rounded-2xl border border-stone-200 bg-stone-50 px-4 py-3 focus-within:border-emerald-500 focus-within:bg-white">
                    <LockClosedIcon className="mr-3 h-5 w-5 text-stone-400" />
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      required
                      className="w-full bg-transparent text-sm text-stone-900 outline-none"
                      placeholder="••••••••"
                    />
                  </div>
                </label>

                {error && (
                  <div className="rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full rounded-2xl bg-[#19342e] px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-[#22453c] disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {isSubmitting ? "Đang đăng nhập..." : "Vào cổng quản trị"}
                </button>
              </form>

              <button
                type="button"
                onClick={() => navigate(GUEST_HOME_PATH)}
                className="mt-6 text-sm font-medium text-stone-500 transition hover:text-stone-900"
              >
                Quay lại trang đặt bàn công khai
              </button>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
