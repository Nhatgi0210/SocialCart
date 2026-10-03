---
name: socialcart-frontend-patterns
description: >-
  Pattern va conventions cho frontend React cua SocialCart. Su dung khi tao
  component moi, implement trang moi, xu ly Socket.IO realtime, goi API,
  hoac can nam chac design system va MUI usage. Bao gom Unified Inbox pattern,
  state management va API layer.
---

# SocialCart Frontend Patterns

## Tech Stack

- React 18 + Vite
- Material UI (MUI) v5
- React Query (server state)
- Zustand (client state)
- Socket.IO Client
- React Router v6

## Cau truc thu muc

```
frontend/src/
    api/              # Axios instances + API functions
        client.js     # Axios base config + interceptors
        auth.js
        conversations.js
        products.js
        orders.js
    components/
        common/       # Button, Modal, Table, etc.
        inbox/        # UnifiedInbox, ConversationList, ChatPanel
        orders/       # OrderCard, OrderStatusChip
        products/     # ProductTable, VariantManager
    hooks/
        useSocket.js  # Socket.IO hook
        useConversations.js
        useOrders.js
    pages/
        InboxPage.jsx
        OrdersPage.jsx
        ProductsPage.jsx
        DashboardPage.jsx
        SettingsPage.jsx
    store/
        authStore.js  # Zustand: user, token
        uiStore.js    # Zustand: sidebar, notifications
    utils/
        formatters.js # Price, date, phone formatters
```

## API Layer Pattern

```javascript
// api/client.js
import axios from "axios";

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// api/conversations.js
export const conversationsApi = {
  getList: (params) => apiClient.get("/conversations", { params }),
  getMessages: (id) => apiClient.get(`/conversations/${id}/messages`),
  sendMessage: (id, data) => apiClient.post(`/conversations/${id}/messages`, data),
  updateStatus: (id, status) => apiClient.patch(`/conversations/${id}/status`, { status }),
};
```

## Socket.IO Hook

```javascript
// hooks/useSocket.js
import { useEffect } from "react";
import { io } from "socket.io-client";
import { useQueryClient } from "@tanstack/react-query";

export function useSocket() {
  const queryClient = useQueryClient();

  useEffect(() => {
    const socket = io(import.meta.env.VITE_SOCKET_URL);

    socket.on("message:new", (data) => {
      queryClient.invalidateQueries(["conversations", data.conversation_id]);
      queryClient.invalidateQueries(["messages", data.conversation_id]);
    });

    socket.on("conversation:updated", () => {
      queryClient.invalidateQueries(["conversations"]);
    });

    return () => socket.disconnect();
  }, [queryClient]);
}
```

## Unified Inbox Layout

```jsx
// pages/InboxPage.jsx - 3 column layout
export default function InboxPage() {
  return (
    <Box sx={{ display: "flex", height: "100vh" }}>
      {/* Left: Conversation List (360px) */}
      <Box sx={{ width: 360, borderRight: 1, borderColor: "divider", overflow: "auto" }}>
        <ConversationList />
      </Box>
      {/* Center: Chat Panel */}
      <Box sx={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <ChatPanel />
      </Box>
      {/* Right Sidebar: Customer + Order Info (300px) */}
      <Box sx={{ width: 300, borderLeft: 1, borderColor: "divider" }}>
        <CustomerInfoPanel />
        <OrderPanel />
      </Box>
    </Box>
  );
}
```

## Conversation Status Chips

```javascript
const STATUS_MAP = {
  unread:      { label: "Chua doc",     color: "error" },
  active:      { label: "Dang xu ly",  color: "warning" },
  ai_active:   { label: "Cho AI",      color: "info" },
  needs_human: { label: "Can can thiep",color: "error" },
  closed:      { label: "Da chot",     color: "success" },
};
```

## Vietnamese Currency Formatter

```javascript
// utils/formatters.js
export const formatVND = (amount) =>
  new Intl.NumberFormat("vi-VN", { style: "currency", currency: "VND" }).format(amount);

export const formatDate = (date) =>
  new Intl.DateTimeFormat("vi-VN", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit"
  }).format(new Date(date));
```

## Env Variables

```
VITE_API_BASE_URL=http://localhost:8000
VITE_SOCKET_URL=http://localhost:8009
```
