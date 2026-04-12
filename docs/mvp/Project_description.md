By removing the liability and technical overhead of in-app payment gateways, we are shifting the platform from a financial escrow to a Social Escrow & Lead Generation model. Your revenue comes entirely from monetizing the Mediators through external subscription tiers.
​

Here is the complete, organized End-to-End (E2E) system description, user flows, and screen architecture for our MVP.

System Overview & Architecture
The platform is a secure Peer-to-Peer (P2P) marketplace for gaming accounts (PUBG, Free Fire, etc.) where safety is enforced by human Mediators rather than automated payment holds. The platform acts as a matchmaker between Buyers, Sellers, and Mediators. All actual fund transfers and credential handoffs happen manually in heavily monitored 3-way chat rooms, after which the Mediator finalizes the digital handshake.

Role Definitions & Permissions
We can divide the platform into three distinct operational roles.

Role	Acquisition	Core Permissions & Limits
Admin	System Default	Full CRUD access, bans users, creates Mediator accounts, manages external Tier assignments.
Mediator	Created by Admin	Verifies external proofs, manages 3-way chats, marks items "Sold". Limited by Tier (max concurrent chats, number of assistant sub-accounts, ability to reopen closed chats, profile badges).
User	Self-Registration	Unified Buyer/Seller role. Can post listings, browse feed, initiate buy requests, and upload external payment/credential proofs in chat.
End-to-End Transaction Flow
Initiation: A User (Buyer) browses the feed, finds an account, and clicks "Request to Buy."

Mediator Selection: The Buyer is navigated to a Mediator Selection screen, displaying available Mediators ranked by their Tier badges and trust scores.

Notification & Routing: Once selected, the system fires push notifications to the Seller and the Mediator.

Chat Generation: The system automatically provisions three distinct real-time chat rooms:

Private: Buyer & Mediator (for sending external payment receipts safely).

Private: Seller & Mediator (for handing over account credentials safely).

Group: Buyer, Seller & Mediator (for general coordination and transparency).

Execution: The Buyer pays the Seller via external methods (Vodafone Cash, Crypto, Bank Transfer) and posts the screenshot. The Seller provides the login credentials to the Mediator.

Resolution: The Mediator verifies the funds are received and the credentials work. The Mediator transfers the credentials to the Buyer.

Closure: The Mediator presses the "Close Deal" button. All three chats instantly become read-only. The account status changes to "Sold" and is moved to the platform's Sold Page and the transaction history of all three participants.

App Navigation & Screens
To keep the MVP focused, the navigation should be separated by role.

1. General User App (Buyer/Seller)
Onboarding/Auth: Sign up, Login, Phone/Email verification.

Home Feed: Infinite scroll of available accounts, filtered by game (PUBG, Free Fire).

Listing Creation: Upload screenshots, description, price, and category.

Mediator Directory: List of Mediators, searchable by Tier, online status, and success rate.

Chat Hub: Inbox showing active negotiation rooms and read-only closed deals.

Profile: User history, active listings, and "Sold" items gallery.

2. Mediator Interface
Dashboard: Queue of incoming "Payment Requests" to accept or decline.

Active Operations (Workspace): A specialized UI showing the 3 synchronized chats for a single deal on one screen.

Deal Management Console: Buttons to "Mark as Sold", "Cancel Deal", or "Reopen Chat" (if their Tier permits).

Assistant Management: A screen to generate login codes for their sub-account assistants based on their Tier limits.

Profile/Tier Status: Shows their current external subscription tier, active limits, and performance badges.