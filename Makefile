# Lối tắt chạy từ thư mục gốc. Backend và frontend độc lập — xem backend/README.md, frontend/README.md.
.PHONY: install test lint api eval web web-install

install:
	$(MAKE) -C backend install

test:
	$(MAKE) -C backend test

lint:
	$(MAKE) -C backend lint

api:
	$(MAKE) -C backend api

eval:
	$(MAKE) -C backend eval

web-install:
	cd frontend && npm install

web:
	cd frontend && npm run dev
