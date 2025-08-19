from ninja import NinjaAPI

api = NinjaAPI()

api.add_router('ons', 'dashboards.ons_extract_pdf.router')

api.add_router('expense', 'backend.expense.api.router')


api.add_router('', 'backend.expense.api.router')
