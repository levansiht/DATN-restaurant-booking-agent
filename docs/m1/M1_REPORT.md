# BAO CAO M1 DATN

## De tai

Xay dung he thong chatbot AI ho tro dat ban nha hang.

## 1. Gioi thieu de tai

### 1.1. Ly do chon de tai

Trong mo hinh van hanh nha hang, khau tiep nhan va xu ly dat ban thuong duoc thuc hien qua dien thoai, tin nhan hoac nhan vien ghi nhan truc tiep. Cach lam nay don gian nhung ton tai nhieu han che:

- De xay ra sai sot khi ghi nham ngay, gio, so luong khach hoac khu vuc ban.
- Kho tra cuu lai thong tin booking khi khach can xac nhan.
- Phu thuoc vao nhan vien, kho phuc vu ngoai gio cao diem hoac ngoai gio hanh chinh.
- Khong tao duoc trai nghiem tu dong va lien mach tren website.

Tu bai toan do, de tai huong den viec xay dung mot he thong dat ban co chatbot AI ho tro hoi thoai tu nhien, tu dong thu thap thong tin, tim ban phu hop va tao booking cho khach hang.

### 1.2. Muc tieu de tai

- Xay dung website dat ban co giao dien than thien.
- Xay dung chatbot AI ho tro hoi thoai dat ban bang tieng Viet.
- Quan ly danh sach ban, tinh trang ban va du lieu booking.
- Ho tro tim ban theo ngay, gio, so nguoi va loai ban.
- Ho tro tao va tra cuu booking qua ma dat ban.
- Ho tro xac thuc nguoi dung co ban bang JWT.

## 2. Dieu tra tong quan va tinh cap thiet

### 2.1. Nhom giai phap hien co tren thi truong

Co the chia cac giai phap lien quan thanh 3 nhom chinh:

#### Nhom 1: Form booking truyen thong

Day la hinh thuc pho bien tren website nha hang. Nguoi dung dien form voi ngay, gio, so luong nguoi va thong tin lien he.

Uu diem:

- Don gian, de trien khai.
- Phu hop voi nha hang quy mo nho.

Han che:

- Trai nghiem mang tinh mot chieu.
- Khong linh hoat khi khach nhap thong tin mo ho nhu "toi mai" hoac "di 4 nguoi".
- Kho ho tro tu van tu nhien.

#### Nhom 2: Chatbot cham soc khach hang

Chatbot duoc dung de tra loi cau hoi, tiep nhan yeu cau va huong dan khach hang.

Uu diem:

- Giao tiep tu nhien hon form.
- Ho tro phuc vu lien tuc 24/7.

Han che:

- Nhieu chatbot chi dung o muc FAQ, khong gan chat voi nghiep vu dat ban.
- Neu khong ket noi du lieu he thong thi khong the tim ban hoac tao booking that.

#### Nhom 3: Nen tang quan ly nha hang

Day la cac he thong co them dashboard quan ly, booking, thong ke, thanh toan va van hanh.

Uu diem:

- Tich hop nhieu quy trinh van hanh.
- Quan ly du lieu tap trung.

Han che:

- He thong lon, chi phi trien khai va tuy bien cao.
- Chua chac toi uu cho mot bai toan chatbot dat ban bang tieng Viet.

### 2.2. Tinh cap thiet cua de tai

De tai co tinh cap thiet vi giai quyet dong thoi ca 3 van de:

- Tu dong hoa tiep nhan yeu cau dat ban.
- Giam tai cho nhan vien trong viec ghi nhan va tra cuu.
- Nang cao trai nghiem nguoi dung thong qua giao tiep hoi thoai.

So voi cac giai phap thong thuong, de tai tap trung vao mot bai toan ro rang: chatbot AI khong chi tra loi ma con tham gia truc tiep vao quy trinh dat ban va xu ly nghiep vu duoc luu trong he thong.

## 3. Hien trang he thong trong repo

Du an hien tai da co cac thanh phan nen tang quan trong:

### 3.1. Frontend

- Su dung React va Vite.
- Co giao dien dat ban.
- Co giao dien chat va tim kiem booking.
- Co lop goi API rieng cho auth, chat, restaurant.

### 3.2. Backend

- Su dung Django REST Framework.
- Cung cap cac nhom API chinh:
  - Auth JWT va thong tin nguoi dung.
  - Chat streaming cho chatbot dat ban.
  - Danh sach ban, tim ban va chi tiet ban.
  - Tao booking, xem booking, huy, xac nhan va tra cuu theo ma.

### 3.3. Database va AI

- PostgreSQL duoc su dung de luu du lieu nguoi dung, ban va booking.
- Agent AI duoc xay dung bang LangChain.
- He thong ho tro su dung OpenAI hoac Claude.
- Co xu ly hoi thoai, streaming token va xu ly bieu thuc thoi gian tieng Viet.

## 4. De xuat giai phap so bo

### 4.1. Mo hinh kien truc

He thong duoc to chuc theo 3 lop:

- Lop giao dien: React/Vite.
- Lop xu ly nghiep vu: Django REST API, chat service, auth service.
- Lop du lieu va AI: PostgreSQL, AI agent, LLM provider.

### 4.2. Cac phan he chinh

- Giao dien dat ban va giao dien chat.
- Phan he xac thuc nguoi dung bang JWT.
- Phan he quan ly ban.
- Phan he quan ly booking.
- Phan he chatbot AI dat ban.

### 4.3. Cong nghe su dung

- React/Vite cho frontend.
- Django REST Framework cho backend.
- PostgreSQL cho co so du lieu.
- LangChain de xay dung agent.
- OpenAI/Claude lam mo hinh ngon ngu lon.
- Docker ho tro dong goi moi truong.

## 5. So do khoi va quy trinh hoat dong

Noi dung nay duoc trinh bay chi tiet trong tep `M1_DIAGRAMS.md`.

Tom tat:

- Nguoi dung thao tac tren frontend.
- Frontend gui yeu cau den backend qua API.
- Backend xu ly auth, booking, table va chat.
- Chat service goi AI agent.
- AI agent khai thac du lieu ban/booking va LLM de hoi thoai.
- Ket qua duoc tra ve frontend va luu vao database khi dat ban thanh cong.

## 6. Du kien ket qua dat duoc

### 6.1. San pham mau

Den cuoi do an, he thong du kien dat duoc:

- Website dat ban cho nguoi dung.
- Chatbot AI ho tro hoi thoai va tu van dat ban.
- Tim ban trong theo ngay, gio, so nguoi va loai ban.
- Tao booking va tra cuu booking.
- He thong tai khoan nguoi dung co ban.

### 6.2. Ket qua hoc thuat

- Bao cao mo ta bai toan, kien truc, du lieu va quy trinh xu ly.
- Bo so do gom so do khoi, quy trinh dat ban, so do co so du lieu.
- Minh chung cho viec ap dung AI vao bai toan nghiep vu cu the.

### 6.3. Huong phat trien

Neu con thoi gian, co the mo rong:

- Dashboard quan tri.
- Thanh toan truc tuyen.
- Thong bao tu dong qua Telegram.

## 7. Phuong phap danh gia va tieu chi kiem thu

### 7.1. Danh gia chuc nang

Can xac nhan he thong dap ung cac tinh huong:

- Tao booking thanh cong voi du lieu hop le.
- Tim dung ban trong theo tieu chi.
- Chatbot hoi du thong tin truoc khi dat ban.
- Tra cuu booking theo ma hoac so dien thoai.

### 7.2. Danh gia chat luong

- Do chinh xac cua luong hoi thoai.
- Toc do phan hoi cua API va chatbot.
- Tinh dung dan cua du lieu booking duoc luu.
- Do on dinh cua cac API chinh.

### 7.3. Chi so de xuat trong bao cao

- Ty le tao booking dung.
- Ty le chatbot thu thap du thong tin.
- Ty le tra ve ban phu hop.
- Ty le API xu ly thanh cong.

M1 chi can chot cach do va tieu chi danh gia, khong can cam ket KPI qua cao khi chua co du lieu thu nghiem lon.

## 8. Ke hoach thuc hien

### Giai doan 1: Hoan thien M1

- Hoan thien bao cao dau ky.
- Ve so do khoi va quy trinh.
- Chuan bi slide bao ve.

### Giai doan 2: Hoan thien luong booking

- Ra soat toan bo luong dat ban dau cuoi.
- Kiem thu API booking, table, search.
- Dong bo giao dien va nghiep vu.

### Giai doan 3: Hoan thien chatbot

- Cai thien prompt.
- Toi uu xu ly ngay gio tieng Viet.
- Nang cao chat luong hoi thoai va tra ve ket qua.

### Giai doan 4: Mo rong neu con thoi gian

- Dashboard admin.
- Payment.
- Thong bao Telegram.

## 9. Phan cong nhom de xuat

Neu thuc hien theo nhom, co the chia:

- Backend: model, API, logic booking, database.
- Frontend: giao dien dat ban, giao dien chat, trang tra cuu.
- AI/Integration: agent, prompt, xu ly thoi gian, danh gia chatbot.
- Documentation: bao cao, slide, so do, tong hop ket qua.

## 10. Ket luan

De tai co tinh thuc tien, co bai toan ro rang va da co nen tang ky thuat trong repo hien tai. M1 can tap trung trinh bay ro su can thiet cua bai toan, giai phap kien truc, san pham du kien, cach danh gia va ke hoach thuc hien. Neu bao cao va slide duoc trinh bay dung huong, de tai co co so tot de chuyen sang cac moc tiep theo.
