# CanteenKart Route Reference

This document summarizes the HTTP routes, grouped by Blueprint, with methods, auth, purpose, and rendered templates.

Legend:
- Auth: public, login-required, owner-only (via `controllers.utils.owner_only`).
- Templates are relative to `templates/`.

## Root
- GET `/` — Home screen.
  - Auth: public
  - Template: `user/home.html`

## Auth (`controllers/auth.py`, blueprint `auth`, url_prefix `/auth`)
- GET `/auth/login` — Login form
  - Auth: public
  - Template: `auth/login.html`
- POST `/auth/login` — Authenticate user
  - Auth: public
  - Redirects to `next` or `/` on success
- GET `/auth/logout` — Logout current user
  - Auth: login-required
  - Redirects to `/auth/login`
- GET `/auth/register` — Registration form
  - Auth: public
  - Template: `auth/signup.html`
- POST `/auth/register` — Create new user and wallet
  - Auth: public
  - Redirects to `/auth/login`

## Menu (`controllers/menu.py`, blueprint `menu`)
- GET `/menu` — Public menu listing
  - Auth: public
  - Template: `user/menu.html`
- GET `/owner/menu` — Owner menu management
  - Auth: owner-only
  - Template: `owner/owner_menu.html`
- POST `/owner/menu/add` — Add a menu item
  - Auth: owner-only
  - Body: `name`, `price`, `description?`, `stock_qty?`, `is_available?`
  - Redirects to `/owner/menu`
- POST `/owner/menu/edit/<item_id>` — Edit a menu item
  - Auth: owner-only
  - Body: same as add (all optional)
  - Redirects to `/owner/menu`
- POST `/owner/menu/delete/<item_id>` — Delete a menu item
  - Auth: owner-only
  - Redirects to `/owner/menu`

## Cart & Orders (User) (`controllers/cart.py`, blueprint `cart`)
- GET `/cart` — Show current cart
  - Auth: public
  - Template: `user/cart.html`
- POST `/cart/add/<item_id>` — Add an item to cart
  - Auth: public
  - Redirects to `/menu`
- POST `/cart/remove/<item_id>` — Remove an item from cart
  - Auth: public
  - Redirects to `/cart`
- GET `/checkout` — Checkout review page
  - Auth: public (prompts login later if needed)
  - Template: `user/checkout.html`
- POST `/checkout` — Place order (requires login)
  - Auth: login-required (enforced in handler)
  - Creates `Order` and `OrderItem`s and emits `new_order` socket event if enabled
  - Redirects to `/order_status/<order_id>`
- GET `/order_status/<order_id>` — Order status page
  - Auth: login-recommended (not strictly enforced)
  - Template: `user/order_status.html`
  - Also: GET `/order_status/<order_id>/qr.png` — QR code image for token/status

## Owner Orders (`controllers/orders.py`, blueprint `owner_orders`)
- GET `/owner/orders` — List active orders (pending, preparing)
  - Auth: owner-only
  - Template: `owner/owner_orders.html`
  - Query: `?status=pending|preparing|ready` to filter
- POST `/owner/orders/<order_id>/status` — Update order status
  - Auth: owner-only
  - Body: `status` in {pending, preparing, ready, completed, cancelled}
  - Emits `order_update` socket event if enabled
  - Redirects to `/owner/orders`

## Owners dashboard & User dashboard (`controllers/owners.py`, blueprint `owners`)
- GET `/owner/dashboard` — Business overview for owners
  - Auth: owner-only
  - Template: `owner/dashboard.html`
- POST `/owner/open` — Toggle canteen open/close in-memory flag
  - Auth: owner-only
- POST `/owner/announcement` — Set simple announcement banner
  - Auth: owner-only
- GET/POST `/owner/scanner` — Token input scanner (MVP for kiosk)
  - Auth: owner-only
- GET `/owner/stock` — Stock & inventory view (Phase 2 base)
  - Auth: owner-only
  - Template: `owner/stock.html`
- POST `/owner/stock/update/<item_id>` — Update stock quantity for an item
  - Auth: owner-only
- POST `/owner/stock/auto_disable` — Disable items with zero stock
  - Auth: owner-only
- GET `/dashboard` — User dashboard for current user
  - Auth: login-required (redirects to `/auth/login` if not logged in)
  - Template: `user/dashboard.html`

## Owner Users (`controllers/owners.py`, blueprint `owners`)
- GET `/owner/users` — List users with stats
  - Auth: owner-only
  - Template: `owner/users_list.html`
- GET `/owner/users/<user_id>` — User detail with orders & activity
  - Auth: owner-only
  - Template: `owner/user_detail.html`

## User pages (`controllers/users.py`, blueprint `users`)
- GET `/orders/history` — My orders list
  - Auth: login-required
  - Template: `user/orders_history.html`
- POST `/orders/<order_id>/reorder` — Add past items to cart
  - Auth: login-required
  - Redirects to `/cart`
- GET/POST `/profile` — View and update basic profile (name)
  - Auth: login-required
  - Template: `user/profile.html`

## Notes
- Access control for owner routes is centralized in `controllers/utils.py` via `@owner_only`.
- Login is handled by Flask-Login; `login_manager.login_view` is `auth.login`.
- Minimal input validation is applied on menu management and status updates to prevent crashes from bad inputs.
- Socket.IO is optional; events are emitted when available.
