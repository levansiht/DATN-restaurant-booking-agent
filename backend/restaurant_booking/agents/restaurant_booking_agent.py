from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from common.services.llm_service import get_llm_service, LLMProvider
from queue import Queue
from restaurant_booking.agents.restaurant_info import RestaurantKnowledgeService
from restaurant_booking.agents.tables import TablesService
from datetime import datetime, timedelta
from restaurant_booking.agents.extract_entity import ConversationEntityExtractor
from restaurant_booking.agents.time_processor import VietnameseTimeProcessor
from restaurant_booking.models import RestaurantProfile


class RestaurantBookingAgent:
    """AI Agent for restaurant booking management"""

    def __init__(
        self,
        callbacks=None,
        queue: Queue = None,
        llm_provider: LLMProvider = LLMProvider.OPENAI,
        sales_handoff: str | None = None,
    ):
        self.callbacks = callbacks
        self.queue = queue
        self.llm_provider = llm_provider
        self.sales_handoff = sales_handoff or ""
        self.llm_service = get_llm_service()
        self.llm = self.llm_service.create_agent_llm(
            provider=llm_provider,
            model=(
                "gpt-4o-mini"
                if llm_provider == LLMProvider.OPENAI
                else "claude-3-sonnet-20240229"
            ),
            # temperature=0.1,
            temperature=0.3,              # 0 = chính xác, ít sáng tạo
            max_tokens=384,
            streaming=True,
            callbacks=self.callbacks,
        )

        # Initialize entity first
        self.entity = {}

        # Initialize services
        self.tables_service = TablesService()
        self.restaurant_knowledge_service = RestaurantKnowledgeService()

        # Initialize tools
        self.tools = self._create_tools()

        # Create agent
        self.agent = self._create_agent()

        # Initialize extract entity
        self.extract_entity = ConversationEntityExtractor(self.llm, callbacks=self.callbacks, queue=self.queue)
        
        # Initialize time processor
        self.time_processor = VietnameseTimeProcessor()

    def _create_tools(self):
        """Create tools for the agent"""
        # Get tools from services
        table_tools = self.tables_service.create_tools()
        knowledge_tools = self.restaurant_knowledge_service.create_tools()

        return table_tools + knowledge_tools

    def _convert_entity_to_string(self, entity: dict) -> str:
        """Convert entity to string"""
        result = ""
        for key, value in entity.items():
            if value is not None:
                result += f"{key}: {value}\n"
        return result

    def _build_sales_handoff_block(self) -> str:
        if not self.sales_handoff:
            return "Chưa có ngữ cảnh tư vấn món cần nối mạch."
        return self.sales_handoff

    def _create_agent(self):
        """Create the agent with tools and prompt"""

        profile = RestaurantProfile.get_active_profile()
        if profile:
            restaurant_name = profile.name
            restaurant_address = profile.address or "Chưa cập nhật"
            restaurant_phone = profile.phone_number or "Chưa cập nhật"
            restaurant_email = profile.email or "Chưa cập nhật"
            restaurant_hours = (
                f"{profile.opening_time.strftime('%H:%M')}-{profile.closing_time.strftime('%H:%M')}"
                if profile.opening_time and profile.closing_time
                else "Chưa cập nhật"
            )
            restaurant_website = profile.website or "Chưa cập nhật"
            restaurant_description = (
                profile.description
                or "Nhà hàng phục vụ khách tại chỗ và hỗ trợ đặt bàn online."
            )
        else:
            restaurant_name = "PSCD Restaurant"
            restaurant_address = "Lô A4-13, Nguyễn Sinh Sắc, Hòa Khánh, Đà Nẵng"
            restaurant_phone = "0906.906.906"
            restaurant_email = "pscds@gmail.com"
            restaurant_hours = "10:00-22:00"
            restaurant_website = "pscd.com"
            restaurant_description = (
                "Phong cách hiện đại, ẩm thực Á-Âu, khu VIP, ngoài trời, đậu xe rộng."
            )
        sales_handoff_block = self._build_sales_handoff_block()

        # System prompt
        system_prompt = """
        PSCD Restaurant Booking Assistant

        Vai trò: Nhân viên tiếp nhận đặt bàn của nhà hàng PSCD. Nói chuyện như nhân viên thật, lịch sự, tự nhiên, ngắn gọn và không vội vàng.

        Thông tin nhà hàng:
        • Tên: {4}
        • Địa chỉ: {5}
        • SĐT: {6} | Email: {7}
        • Giờ: {8} | Website: {9}
        • Đặc điểm: {10}

        Ngữ cảnh chuyển tiếp từ tư vấn món:
        {11}

        Phong cách giao tiếp:
        • Xưng hô mặc định khi chưa biết tên: mình - em
        • Khi biết tên khách, ưu tiên xưng theo tên khách thay vì lặp lại “anh/chị”
        • Nếu đầu cuộc trò chuyện chưa biết tên, hỏi tên nhẹ nhàng để tiện xưng hô rồi tiếp tục hỗ trợ
        • Không xưng "tôi"
        • Không chủ động tự giới thiệu là AI, bot hay trợ lý ảo; nếu khách hỏi trực tiếp thì nói minh bạch đây là trợ lý tự động của nhà hàng
        • Có thể mở lời nối mạch rất ngắn từ ngữ cảnh món ăn nếu có, rồi quay lại việc đặt bàn
        • Luôn thân thiện, tự nhiên, lễ phép và giống nhân viên thật
        • Mỗi lượt chỉ hỏi tối đa 2 thông tin gần nhau. Không biến hội thoại thành form
        • Nếu khách đã cung cấp thông tin nào thì không hỏi lại thông tin đó
        • Nếu khách trả lời mơ hồ, phải hỏi lại ngắn gọn để làm rõ
        • Có thể dùng tiếng Việt hoặc tiếng Anh theo ngữ cảnh của khách

        Chỉ bắt đầu quy trình đặt bàn khi khách thực sự đang muốn đặt/giữ bàn hoặc đang trả lời tiếp một câu hỏi booking trước đó.
        Nếu khách hỏi menu, khoảng giá, giờ mở cửa, địa chỉ, số điện thoại hoặc gợi ý món thì KHÔNG đẩy sang booking.
        Với câu hỏi thông tin nhà hàng hoặc menu, phải ưu tiên dùng tool get_restaurant_info, search_menu_items hoặc suggest_menu_by_budget để trả lời bằng dữ liệu thật.

        QUY TRÌNH BOOKING PHẢI ĐI THEO THỨ TỰ SAU

        Bước 1: Xác nhận nhẹ nhu cầu đặt bàn nếu cần.
        • Nếu khách vừa nói rõ muốn đặt/giữ bàn và chưa biết tên khách, có thể đáp: “Dạ em hỗ trợ đặt bàn cho mình ạ. Mình cho em xin tên để tiện xưng hô nhé?”
        • Nếu đã biết tên khách, dùng tên đó trong câu trả lời.
        • Không hỏi lại câu “mình có muốn đặt bàn không” nếu khách đã nói quá rõ.

        Bước 2: Thu thập thời gian dùng bữa.
        • Nếu thiếu cả ngày và giờ: hỏi cùng một lượt “Dạ mình muốn đặt ngày nào và khoảng mấy giờ ạ?”
        • Nếu thiếu ngày: chỉ hỏi ngày.
        • Nếu thiếu giờ: chỉ hỏi giờ.

        Bước 3: Thu thập số người.
        • Nếu chưa có party_size: hỏi “Dạ mình đi mấy người để em kiểm tra bàn phù hợp ạ?”

        Bước 4: Thu thập vị trí ngồi.
        • Nếu chưa có table_type và floor: hỏi cùng một lượt.
        • Có thể gợi ý các lựa chọn: trong nhà, ngoài trời, phòng riêng, quầy bar, ghế ngồi, gần cửa sổ; tầng 1 hoặc tầng 2.

        Bước 5: Tìm bàn và mời khách chọn.
        • Chỉ gọi tool search_tables khi đã có đủ booking_date, booking_time, party_size, table_type, floor.
        • Kết quả phải nêu được table_id để khách chọn.
        • Nếu có nhiều bàn phù hợp, mời khách chọn rõ bàn nào.
        • Nếu chỉ có 1 bàn phù hợp, hỏi xác nhận trước khi đi tiếp.
        • Nếu không có bàn phù hợp, xin lỗi ngắn gọn và hỏi khách muốn đổi giờ / khu vực / tầng nào.

        Bước 6: Thu thập thông tin liên hệ sau khi khách đã chọn bàn.
        • Hỏi guest_name + guest_phone cùng một lượt.
        • Sau đó hỏi guest_email.
        • Chỉ hỏi note sau khi đã có đủ tên, số điện thoại và email.
        • Nếu khách không có ghi chú thì bỏ qua note.

        Bước 7: Xác nhận và đặt bàn.
        • Khi đã đủ thông tin, gọi tool summary_booking_info để tóm tắt.
        • Chỉ gọi book_table khi khách xác nhận rõ bằng các ý như “đúng rồi”, “ok”, “đồng ý”, “chính xác”.
        • Nếu khách chưa xác nhận rõ, tiếp tục yêu cầu xác nhận, không được gọi book_table.
        • book_table là nguồn xác nhận cuối cùng. Nếu tool báo hết bàn / xung đột, phải xin lỗi ngắn gọn và mời khách chọn bàn khác.
        • Nếu tool trả về hướng dẫn thanh toán SePay hoặc trang tra cứu booking, phải giữ nguyên ý chính đó khi phản hồi cho khách.

        Nguyên tắc bắt buộc:
        • Không hỏi dồn dập quá 2 thông tin gần nhau trong một lượt.
        • Không bịa hoặc tự điền thông tin khách chưa cung cấp.
        • Không tuyên bố đặt bàn thành công nếu tool book_table chưa xác nhận thành công.
        • Nếu khách chỉ trả lời thêm một phần thông tin, hãy ghi nhận phần đó và hỏi tiếp đúng phần còn thiếu kế tiếp.
        • Khi đã vào luồng booking, không quay lại tư vấn món dài dòng trừ khi khách đổi ý rõ ràng.

        với table_type là loại bàn, chỉ lấy một trong các giá trị: "INDOOR" (Trong nhà), "OUTDOOR" (Ngoài trời), "PRIVATE" (Phòng riêng), "BAR" (Quầy bar), "BOOTH" (Ghế ngồi), "WINDOW" (Cửa sổ)
        với floor là tầng, chỉ lấy một trong các giá trị: 1, 2
        với party_size là số lượng người, chỉ lấy một trong các giá trị: 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20
        với booking_date là ngày đặt bàn, chỉ lấy một trong các giá trị: "YYYY-MM-DD"
        với booking_time là giờ đặt bàn, chỉ lấy một trong các giá trị: "HH:MM"
        với table_id là id bàn
        với guest_name là tên khách
        với guest_phone là số điện thoại khách
        với guest_email là email khách
        với note là ghi chú của khách hàng. Có thể để trống

        Các quy tắt về ngày giờ:
        - Hôm nay là ngày {0}
        - Ngày hôm qua là ngày {1}
        - Ngày mai là ngày {2}
        - Hôm nay là thứ {3}
        - Ngày đặt bàn không được ở trong quá khứ.
        - Khi khách hàng chưa cung cấp ngày đặt bàn, hãy hỏi lại.
        - Khi khách hàng chưa cung cấp giờ đặt bàn, hãy hỏi lại.

        """
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        today_weekday = datetime.now().weekday() + 2 

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt.format(
                        today,
                        yesterday,
                        tomorrow,
                        today_weekday,
                        restaurant_name,
                        restaurant_address,
                        restaurant_phone,
                        restaurant_email,
                        restaurant_hours,
                        restaurant_website,
                        restaurant_description,
                        sales_handoff_block,
                    ),
                ),
                MessagesPlaceholder(variable_name="history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        # Create agent
        agent = create_openai_tools_agent(llm=self.llm, tools=self.tools, prompt=prompt)

        memory_instance = ConversationBufferMemory(
            memory_key="history",
            return_messages=True,
        )

        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=memory_instance,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10,
            callbacks=self.callbacks
        )

    def _update_agent_with_entity(self):
        """Update the agent with current entity information by recreating it"""
        # Store current memory
        current_memory = self.agent.memory
        
        # Recreate agent with updated entity
        self.agent = self._create_agent()
        
        # Restore memory
        self.agent.memory = current_memory

    def _preprocess_time_expressions(self, user_input: str) -> str:
        """
        Xử lý các biểu thức thời gian trong input của user
        """
        # Kiểm tra xem có chứa biểu thức thời gian không
        if self.time_processor.is_time_expression(user_input):
            # Cải thiện khả năng hiểu thời gian
            enhanced_input = self.time_processor.enhance_time_understanding(user_input)
            print(f"=========================== Time processing:")
            print(f"Original input: {user_input}")
            print(f"Enhanced input: {enhanced_input}")
            return enhanced_input
        
        return user_input

    def run(self, user_input: str) -> str:
        """Invoke the agent"""
        print("===========================Memory:")
        print(self.agent.memory.chat_memory.messages)
        
        # Xử lý thời gian trước khi gửi cho agent
        processed_input = self._preprocess_time_expressions(user_input)
        
        # extract entity
        # self.entity = self.extract_entity.extract(self.agent.memory.chat_memory.messages, user_input)
        
        # # Update the agent with new entity information
        # self._update_agent_with_entity()
        
        return self.agent.invoke({"input": processed_input})
