-- I/K/S combinator seed: the atomic building blocks of computation.
-- No arithmetic, no geometry, no theorems — just pure combination.
universe u v w

def I {α : Sort u} (x : α) : α := x
def K {α : Sort u} {β : Sort v} (x : α) (_ : β) : α := x
def S {α : Sort u} {β : Sort v} {γ : Sort w}
    (f : α → β → γ) (g : α → β) (x : α) : γ :=
  f x (g x)
