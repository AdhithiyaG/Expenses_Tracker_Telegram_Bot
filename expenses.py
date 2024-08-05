class Expense:
    def __init__(self,name,category,amount,description,date) -> None:
        self.name=name
        self.category=category
        self.amount=amount
        self.description=description
        self.date=date

    def __repr__(self):
        return f" <Expense : {self.name},{self.category},₹ {self.amount:.2f},{self.description},{self.date}> "
    