// SocialCart Prototype — Mock Data
// Dependency-free, backend-free. State resets on reload.

const MOCK_DATA = {
  seller: {
    id: 'seller-001',
    name: 'Nguyễn Thị Lan',
    email: 'lan@socialsells.vn',
    password: 'demo123',
    avatar: 'NL',
    shop: 'Shop Thời Trang Lan'
  },

  conversations: [
    {
      id: 'conv-001',
      customerName: 'Trần Minh Khoa',
      customerAvatar: 'TK',
      platform: 'facebook',
      unread: true,
      lastMessage: 'Em muốn hỏi về size áo ạ, áo này còn size L không?',
      lastMessageIsAI: false,
      timestamp: new Date(Date.now() - 3 * 60 * 1000), // 3 phút trước
      aiStatus: 'need-seller',
      processingStatus: 'Đang xử lý',
      messages: [
        { id: 'm1', type: 'customer', text: 'Chào shop ạ, em thấy bên mình có áo phông xanh cute lắm', time: new Date(Date.now() - 25 * 60 * 1000) },
        { id: 'm2', type: 'ai', text: 'Chào bạn Khoa! 👋 Cảm ơn bạn đã quan tâm đến sản phẩm của Shop Thời Trang Lan. Bạn đang hỏi về áo phông xanh nào ạ? Shop có nhiều mẫu lắm, bạn có thể cho mình biết thêm thông tin không ạ?', time: new Date(Date.now() - 24 * 60 * 1000) },
        { id: 'm3', type: 'customer', text: 'Áo phông oversize màu xanh navy ý ạ, giá bao nhiêu vậy shop?', time: new Date(Date.now() - 20 * 60 * 1000) },
        { id: 'm4', type: 'ai', text: 'Dạ áo phông oversize navy của shop giá 285.000đ ạ! Áo có 4 size: S, M, L, XL. Chất liệu cotton 100%, thoáng mát, giặt máy được. Bạn muốn đặt size nào ạ? 😊', time: new Date(Date.now() - 19 * 60 * 1000) },
        { id: 'm5', type: 'customer', text: 'Em muốn hỏi về size áo ạ, áo này còn size L không?', time: new Date(Date.now() - 3 * 60 * 1000) },
        { id: 'm6', type: 'system', text: '🔔 AI gặp lỗi. Hội thoại cần bạn xử lý.', time: new Date(Date.now() - 2 * 60 * 1000), isHandoff: true }
      ],
      customer: {
        name: 'Trần Minh Khoa',
        platform: 'Facebook',
        platformUsername: '@tranminhkhoa',
        phone: '',
        orders: [],
        notes: 'Khách hay hỏi size L'
      }
    },
    {
      id: 'conv-002',
      customerName: 'Lê Thị Hương',
      customerAvatar: 'LH',
      platform: 'zalo',
      unread: true,
      lastMessage: 'AI: Đơn hàng của bạn đang được xử lý, dự kiến giao trong 2-3 ngày ạ',
      lastMessageIsAI: true,
      timestamp: new Date(Date.now() - 12 * 60 * 1000), // 12 phút
      aiStatus: 'ai-active',
      processingStatus: 'Đang xử lý',
      messages: [
        { id: 'm1', type: 'customer', text: 'Shop ơi đơn 98765 của mình đến chưa vậy?', time: new Date(Date.now() - 15 * 60 * 1000) },
        { id: 'm2', type: 'ai', text: 'Chào bạn Hương! Mình kiểm tra đơn hàng #98765 nhé. Đơn của bạn hiện đang ở kho giao hàng Bình Dương, dự kiến giao đến địa chỉ của bạn trong 2-3 ngày làm việc ạ. Bạn có thể theo dõi tại link: ghtk.vn/... 📦', time: new Date(Date.now() - 14 * 60 * 1000) },
        { id: 'm3', type: 'customer', text: 'Oke shop, cảm ơn nhé', time: new Date(Date.now() - 13 * 60 * 1000) },
        { id: 'm4', type: 'ai', text: 'Đơn hàng của bạn đang được xử lý, dự kiến giao trong 2-3 ngày ạ. Nếu cần hỗ trợ thêm bạn nhắn cho shop nhé! 🌸', time: new Date(Date.now() - 12 * 60 * 1000) }
      ],
      customer: {
        name: 'Lê Thị Hương',
        platform: 'Zalo',
        platformUsername: '0912 345 678',
        phone: '0912345678',
        orders: [
          { id: '#98765', status: 'Đang giao', product: 'Váy hoa nhí size M', amount: '380.000đ', date: '20/09/2026' }
        ],
        notes: ''
      }
    },
    {
      id: 'conv-003',
      customerName: 'Phạm Văn Đức',
      customerAvatar: 'PĐ',
      platform: 'facebook',
      unread: false,
      lastMessage: 'Cảm ơn shop, mình sẽ đặt hàng sau nhé',
      lastMessageIsAI: false,
      timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000), // 2 giờ trước
      aiStatus: 'seller-handling',
      processingStatus: 'Đã xử lý',
      messages: [
        { id: 'm1', type: 'customer', text: 'Shop cho mình hỏi quần jean nam size 32 còn không?', time: new Date(Date.now() - 3 * 60 * 60 * 1000) },
        { id: 'm2', type: 'ai', text: 'Chào bạn Đức! Shop có quần jean nam nhiều size lắm ạ. Size 32 hiện đang có đủ. Giá từ 420.000đ, bạn muốn xem mẫu nào không?', time: new Date(Date.now() - 3 * 60 * 60 * 1000 + 1 * 60 * 1000) },
        { id: 'm3', type: 'system', text: 'Người bán đã tiếp nhận hội thoại', time: new Date(Date.now() - 2.5 * 60 * 60 * 1000), isHandoff: false },
        { id: 'm4', type: 'seller', text: 'Chào bạn, mình là Lan, chủ shop nè. Quần jean slim fit size 32 đang có đủ màu: đen, xanh đậm, xanh nhạt. Bạn thích màu nào ạ?', time: new Date(Date.now() - 2.4 * 60 * 60 * 1000) },
        { id: 'm5', type: 'customer', text: 'Cảm ơn shop, mình sẽ đặt hàng sau nhé', time: new Date(Date.now() - 2 * 60 * 60 * 1000) }
      ],
      customer: {
        name: 'Phạm Văn Đức',
        platform: 'Facebook',
        platformUsername: '@phamvanduc.style',
        phone: '',
        orders: [],
        notes: 'Quan tâm quần jean nam'
      }
    },
    {
      id: 'conv-004',
      customerName: 'Nguyễn Thu Thảo',
      customerAvatar: 'NT',
      platform: 'zalo',
      unread: false,
      lastMessage: 'AI: Cảm ơn bạn đã mua sắm tại Shop Thời Trang Lan!',
      lastMessageIsAI: true,
      timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000),
      aiStatus: 'ai-active',
      processingStatus: 'Đã xử lý',
      messages: [
        { id: 'm1', type: 'customer', text: 'Shop ơi mình muốn đặt áo dài cách tân size S ạ', time: new Date(Date.now() - 6 * 60 * 60 * 1000) },
        { id: 'm2', type: 'ai', text: 'Chào bạn Thảo! Áo dài cách tân size S của shop có 3 màu: trắng tinh, xanh pastel, hồng nhạt. Giá 650.000đ/chiếc. Bạn muốn chọn màu nào và địa chỉ giao hàng ạ?', time: new Date(Date.now() - 5.9 * 60 * 60 * 1000) },
        { id: 'm3', type: 'customer', text: 'Màu trắng nha shop, giao về 123 Nguyễn Trãi Q5 HCM ạ', time: new Date(Date.now() - 5.5 * 60 * 60 * 1000) },
        { id: 'm4', type: 'ai', text: 'Mình đã ghi nhận đơn hàng: Áo dài cách tân trắng size S - 650.000đ. Giao về 123 Nguyễn Trãi Q5 HCM. Bạn xác nhận thông tin đúng không ạ?', time: new Date(Date.now() - 5.4 * 60 * 60 * 1000) },
        { id: 'm5', type: 'customer', text: 'Đúng rồi ạ', time: new Date(Date.now() - 5.2 * 60 * 60 * 1000) },
        { id: 'm6', type: 'ai', text: 'Cảm ơn bạn đã mua sắm tại Shop Thời Trang Lan! Đơn hàng sẽ được giao trong 2-3 ngày. Shop sẽ liên hệ khi hàng sắp giao nhé! 🌸', time: new Date(Date.now() - 5 * 60 * 60 * 1000) }
      ],
      customer: {
        name: 'Nguyễn Thu Thảo',
        platform: 'Zalo',
        platformUsername: '0987 654 321',
        phone: '0987654321',
        orders: [
          { id: '#99123', status: 'Chờ xác nhận', product: 'Áo dài cách tân trắng size S', amount: '650.000đ', date: '24/09/2026' }
        ],
        notes: 'Khách VIP, hay mua áo trắng'
      }
    },
    {
      id: 'conv-005',
      customerName: 'Hoàng Bảo Ngọc',
      customerAvatar: 'HN',
      platform: 'facebook',
      unread: false,
      lastMessage: 'Size M thì bao nhiêu tiền vậy shop?',
      lastMessageIsAI: false,
      timestamp: new Date(Date.now() - 24 * 60 * 60 * 1000), // hôm qua
      aiStatus: 'ai-active',
      processingStatus: 'Mới',
      messages: [
        { id: 'm1', type: 'customer', text: 'Size M thì bao nhiêu tiền vậy shop?', time: new Date(Date.now() - 24 * 60 * 60 * 1000) }
      ],
      customer: {
        name: 'Hoàng Bảo Ngọc',
        platform: 'Facebook',
        platformUsername: '@hoangbaongoc',
        phone: '',
        orders: [],
        notes: ''
      }
    }
  ],

  products: [
    {
      id: 'prod-001',
      name: 'Áo phông oversize',
      variants: [
        { id: 'v1', name: 'S - Xanh navy', price: 285000, stock: 15 },
        { id: 'v2', name: 'M - Xanh navy', price: 285000, stock: 8 },
        { id: 'v3', name: 'L - Xanh navy', price: 285000, stock: 3 },
        { id: 'v4', name: 'XL - Xanh navy', price: 285000, stock: 0 },
        { id: 'v5', name: 'S - Trắng', price: 285000, stock: 20 },
        { id: 'v6', name: 'M - Trắng', price: 285000, stock: 12 },
        { id: 'v7', name: 'L - Trắng', price: 285000, stock: 5 }
      ]
    },
    {
      id: 'prod-002',
      name: 'Váy hoa nhí',
      variants: [
        { id: 'v8', name: 'S - Hoa đỏ', price: 380000, stock: 6 },
        { id: 'v9', name: 'M - Hoa đỏ', price: 380000, stock: 4 },
        { id: 'v10', name: 'L - Hoa đỏ', price: 380000, stock: 2 },
        { id: 'v11', name: 'S - Hoa xanh', price: 380000, stock: 0 },
        { id: 'v12', name: 'M - Hoa xanh', price: 380000, stock: 7 }
      ]
    },
    {
      id: 'prod-003',
      name: 'Áo dài cách tân',
      variants: [
        { id: 'v13', name: 'S - Trắng tinh', price: 650000, stock: 3 },
        { id: 'v14', name: 'M - Trắng tinh', price: 650000, stock: 5 },
        { id: 'v15', name: 'S - Xanh pastel', price: 650000, stock: 2 },
        { id: 'v16', name: 'M - Xanh pastel', price: 650000, stock: 4 },
        { id: 'v17', name: 'S - Hồng nhạt', price: 650000, stock: 1 }
      ]
    },
    {
      id: 'prod-004',
      name: 'Quần jean slim fit nam',
      variants: [
        { id: 'v18', name: '30 - Đen', price: 420000, stock: 8 },
        { id: 'v19', name: '32 - Đen', price: 420000, stock: 10 },
        { id: 'v20', name: '34 - Đen', price: 420000, stock: 4 },
        { id: 'v21', name: '32 - Xanh đậm', price: 420000, stock: 7 },
        { id: 'v22', name: '32 - Xanh nhạt', price: 420000, stock: 3 }
      ]
    }
  ]
};
