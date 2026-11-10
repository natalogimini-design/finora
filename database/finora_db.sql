-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Waktu pembuatan: 10 Nov 2026 pada 05.19
-- Versi server: 8.4.3
-- Versi PHP: 8.3.16

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `finora_db`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `accounts`
--

CREATE TABLE `accounts` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `account_number` varchar(30) NOT NULL,
  `balance` decimal(15,2) DEFAULT '0.00',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data untuk tabel `accounts`
--

INSERT INTO `accounts` (`id`, `user_id`, `account_number`, `balance`, `created_at`) VALUES
(1, 1, 'FIN842195644', 1200000.00, '2026-11-07 11:51:35'),
(2, 2, 'FIN563312920', 0.00, '2026-11-09 09:17:16'),
(3, 3, 'FIN506243433', 150000.00, '2026-11-10 04:38:56');

-- --------------------------------------------------------

--
-- Struktur dari tabel `autopay`
--

CREATE TABLE `autopay` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `category` varchar(50) NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `payment_date` int NOT NULL,
  `status` enum('active','inactive') DEFAULT 'active',
  `last_paid` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `investments`
--

CREATE TABLE `investments` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `type` varchar(50) NOT NULL,
  `capital` decimal(15,2) NOT NULL,
  `current_value` decimal(15,2) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `notifications`
--

CREATE TABLE `notifications` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `title` varchar(150) NOT NULL,
  `message` text NOT NULL,
  `is_read` tinyint(1) DEFAULT '0',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `payments`
--

CREATE TABLE `payments` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `category` varchar(50) NOT NULL,
  `customer_number` varchar(100) DEFAULT NULL,
  `amount` decimal(15,2) NOT NULL,
  `status` enum('success','failed','pending') DEFAULT 'pending',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `savings`
--

CREATE TABLE `savings` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `target_amount` decimal(15,2) NOT NULL,
  `current_amount` decimal(15,2) DEFAULT '0.00',
  `target_date` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `savings_goals`
--

CREATE TABLE `savings_goals` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `target_amount` decimal(15,2) NOT NULL,
  `saved_amount` decimal(15,2) DEFAULT '0.00',
  `deadline` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `savings_history`
--

CREATE TABLE `savings_history` (
  `id` int NOT NULL,
  `savings_id` int NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `type` enum('deposit','withdraw') NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `spending_limits`
--

CREATE TABLE `spending_limits` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `month` int NOT NULL,
  `year` int NOT NULL,
  `limit_amount` decimal(15,2) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `transactions`
--

CREATE TABLE `transactions` (
  `id` int NOT NULL,
  `user_id` int NOT NULL,
  `type` enum('income','expense','transfer_in','transfer_out','topup','payment','interest') NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data untuk tabel `transactions`
--

INSERT INTO `transactions` (`id`, `user_id`, `type`, `amount`, `description`, `created_at`) VALUES
(1, 1, 'topup', 1000000.00, 'Top Up - Simulasi', '2026-11-09 08:55:09'),
(2, 1, 'income', 100000.00, 'Top Up via Simulasi', '2026-11-10 04:34:03'),
(3, 1, 'income', 250000.00, 'Top Up via Simulasi', '2026-11-10 05:04:46');

-- --------------------------------------------------------

--
-- Struktur dari tabel `transfers`
--

CREATE TABLE `transfers` (
  `id` int NOT NULL,
  `sender_account_id` int NOT NULL,
  `receiver_account_id` int NOT NULL,
  `amount` decimal(15,2) NOT NULL,
  `note` varchar(255) DEFAULT NULL,
  `status` varchar(20) NOT NULL DEFAULT 'success',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data untuk tabel `transfers`
--

INSERT INTO `transfers` (`id`, `sender_account_id`, `receiver_account_id`, `amount`, `note`, `status`, `created_at`) VALUES
(1, 1, 3, 200000.00, NULL, 'success', '2026-11-10 04:48:39'),
(2, 3, 1, 50000.00, NULL, 'success', '2026-11-10 05:04:19');

-- --------------------------------------------------------

--
-- Struktur dari tabel `users`
--

CREATE TABLE `users` (
  `id` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `pin_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data untuk tabel `users`
--

INSERT INTO `users` (`id`, `name`, `email`, `password_hash`, `pin_hash`, `created_at`) VALUES
(1, 'user', 'user123@finance.com', 'scrypt:32768:8:1$glNfKLwcEFtvBC93$dc2ce001ed9be8bdaf2fb12084d404e6a7a7f1cc4e16cb15b190863f24451537718a8eb9b7814072d570805ef710d264de8fc34468d1dcb0779642ed3dbe0023', 'scrypt:32768:8:1$SeluOAER4Xy37hqR$d2e94122616b144f46e1988f2aeaf8be34217c9a66f1dd48212788ef713c98d3668d7a02b24d47959aa0b394e363d5dd81593b7d686691c5f94773f92e6e95d7', '2026-11-07 11:51:35'),
(2, 'mini', 'mini123@finance.com', 'scrypt:32768:8:1$OAMoeYRxuBF8pFAK$c1eae67fc9ca8dea2fa8dc0b8dd33dfec40d8805f2789c250bf4d6f28b52c9c66690771ca9f7c49f6bba45b5eb9017b02271defda59946ef6a9a98ac2b19cdb7', 'scrypt:32768:8:1$GollpjTuXjiiGp5p$f778f4ae5e7dde1d1b18ad052e6deddef628e0d36087e556ad332be6b99e395df9318e81580878dc23eb366250caa3ff062ecde2335a8b8d60fba1ea5cfb867d', '2026-11-09 09:17:16'),
(3, 'Natalogi', 'natalogi123@finance.com', 'scrypt:32768:8:1$sJgl2Dyb3thj30jm$2340eb3b770fd92286ca49cb246ade8db3ef02aecfb9e7e005ff44d848ecd678c4c61460e1d902b0d259841365eb99b0c93ec73e1e4348078e3483bfc6f904e0', 'scrypt:32768:8:1$MiqsE1J3v3fxosyU$ebb1f48ee4d83045e76863c601c084ca0fbb98eab504d20f1aa07506d1c7031997e477842c272d247d926154afcc75b93c5f48c42786795f5423ebde4cce0b60', '2026-11-10 04:38:56');

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `accounts`
--
ALTER TABLE `accounts`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `account_number` (`account_number`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `autopay`
--
ALTER TABLE `autopay`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `investments`
--
ALTER TABLE `investments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `notifications`
--
ALTER TABLE `notifications`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `payments`
--
ALTER TABLE `payments`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `savings`
--
ALTER TABLE `savings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `savings_goals`
--
ALTER TABLE `savings_goals`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `savings_history`
--
ALTER TABLE `savings_history`
  ADD PRIMARY KEY (`id`),
  ADD KEY `savings_id` (`savings_id`);

--
-- Indeks untuk tabel `spending_limits`
--
ALTER TABLE `spending_limits`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_user_month` (`user_id`,`month`,`year`);

--
-- Indeks untuk tabel `transactions`
--
ALTER TABLE `transactions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indeks untuk tabel `transfers`
--
ALTER TABLE `transfers`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sender_account_id` (`sender_account_id`),
  ADD KEY `receiver_account_id` (`receiver_account_id`);

--
-- Indeks untuk tabel `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `accounts`
--
ALTER TABLE `accounts`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT untuk tabel `autopay`
--
ALTER TABLE `autopay`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `investments`
--
ALTER TABLE `investments`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `notifications`
--
ALTER TABLE `notifications`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `payments`
--
ALTER TABLE `payments`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `savings`
--
ALTER TABLE `savings`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `savings_goals`
--
ALTER TABLE `savings_goals`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `savings_history`
--
ALTER TABLE `savings_history`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `spending_limits`
--
ALTER TABLE `spending_limits`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT untuk tabel `transactions`
--
ALTER TABLE `transactions`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT untuk tabel `transfers`
--
ALTER TABLE `transfers`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT untuk tabel `users`
--
ALTER TABLE `users`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `accounts`
--
ALTER TABLE `accounts`
  ADD CONSTRAINT `accounts_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `autopay`
--
ALTER TABLE `autopay`
  ADD CONSTRAINT `autopay_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `investments`
--
ALTER TABLE `investments`
  ADD CONSTRAINT `investments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `notifications`
--
ALTER TABLE `notifications`
  ADD CONSTRAINT `notifications_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `payments`
--
ALTER TABLE `payments`
  ADD CONSTRAINT `payments_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `savings`
--
ALTER TABLE `savings`
  ADD CONSTRAINT `savings_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `savings_goals`
--
ALTER TABLE `savings_goals`
  ADD CONSTRAINT `savings_goals_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `savings_history`
--
ALTER TABLE `savings_history`
  ADD CONSTRAINT `savings_history_ibfk_1` FOREIGN KEY (`savings_id`) REFERENCES `savings` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `spending_limits`
--
ALTER TABLE `spending_limits`
  ADD CONSTRAINT `spending_limits_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `transactions`
--
ALTER TABLE `transactions`
  ADD CONSTRAINT `transactions_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Ketidakleluasaan untuk tabel `transfers`
--
ALTER TABLE `transfers`
  ADD CONSTRAINT `transfers_ibfk_1` FOREIGN KEY (`sender_account_id`) REFERENCES `accounts` (`id`),
  ADD CONSTRAINT `transfers_ibfk_2` FOREIGN KEY (`receiver_account_id`) REFERENCES `accounts` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
