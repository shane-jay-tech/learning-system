# C++ 继承与多态

## 继承基础

```cpp
class Animal {
public:
    string name;
    Animal(string n) : name(n) {}
    void greet() { cout << "Hi, I'm " << name << endl; }
};

class Dog : public Animal {              // 公有继承
public:
    Dog(string n) : Animal(n) {}         // 调父类构造
    void bark() { cout << "Woof!" << endl; }
};

Dog d("Rex");
d.greet();    // Hi, I'm Rex （继承自父类）
d.bark();     // Woof!
```

`class Dog : public Animal` 表示"Dog 公开继承 Animal"——子类自动获得父类的 public 成员。

## 三种继承（public / protected / private）

| 继承方式 | 父类 public 在子类变 | 父类 protected 在子类变 |
|---|---|---|
| `public` | public（**最常用**） | protected |
| `protected` | protected | protected |
| `private` | private | private |

**99% 用 public**——保持父类的接口可见。

## virtual：让方法可被重写

```cpp
class Animal {
public:
    virtual void speak() {                // 注意 virtual
        cout << "some sound" << endl;
    }
    virtual ~Animal() = default;            // 析构也要 virtual
};

class Dog : public Animal {
public:
    void speak() override {                 // override 关键字（C++11+）
        cout << "Woof!" << endl;
    }
};
```

`virtual` 让 C++ 知道"这个方法可能被子类重写"——通过指针/引用调用时**动态分派到真实类型**。

## 多态：用基类指针调子类方法

```cpp
Animal* a = new Dog("Rex");
a->speak();       // Woof! —— 因为 virtual + 实际是 Dog
delete a;
```

没 `virtual` 的话 `a->speak()` 会调 Animal 的版本（静态分派）——这是新手最常踩的坑。

## override 关键字（强烈建议加）

```cpp
class Dog : public Animal {
public:
    void speak() override {           // 编译器检查：父类必须真有 speak
        ...
    }
};
```

打错名（如 `speack`）时 `override` 让编译器立即报错。**不写 override 是 bug 滋生地**。

## 抽象类（纯虚函数）

```cpp
class Shape {
public:
    virtual double area() const = 0;     // 纯虚函数
    virtual ~Shape() = default;
};

// Shape s;   // 错！抽象类不能实例化

class Circle : public Shape {
public:
    double r;
    Circle(double r) : r(r) {}
    double area() const override {
        return 3.14159 * r * r;
    }
};
```

`= 0` 让方法成为"必须重写"——子类不重写也不能实例化。

## 析构函数为什么要 virtual

```cpp
Animal* a = new Dog("Rex");
delete a;     // 不写 virtual ~Animal()，只调 Animal 的析构 → 内存泄漏
```

**只要类里有 virtual 方法，析构函数也必须 virtual**——这是 C++ 铁律。

## 常见错误

1. **忘 virtual**：基类指针调用时调到错误版本
2. **析构非 virtual + new 子类**：内存泄漏，子类析构不被调
3. **派生类构造没初始化父类**：构造函数初始化列表必须显式调父类构造（除非父类有默认构造）
4. **用值传 polymorphic 对象**：`void f(Animal a)` 会**切片**（slicing）——子类部分被砍掉

## 现在做练习

5 道题：基础继承、virtual + 多态、override 强制、纯虚抽象类、虚析构。
