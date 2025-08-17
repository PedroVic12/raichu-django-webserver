from django.shortcuts import render


def index(request):
    template_name = 'core/index.html'
    return render(request, template_name)

def expense_list(request):
    template_name = 'expense/expense.html'
    form = ExpenseForm()
    context = {'form': form}
    return render(request, template_name, context)


