"""
v2struct - 将变量打包/解包到/从标量结构
这是MATLAB v2struct的Python转换版本
"""
import inspect
import sys


def v2struct(*args, **kwargs):
    """
    v2struct具有双重功能：将变量打包到结构中，以及从结构中解包变量
    
    打包用法:
        S = v2struct(x, y, z, ...)  # 使用变量名作为字段名
        S = v2struct(**{'x': x, 'y': y})  # 使用关键字参数
    
    解包用法:
        x, y, z = v2struct(S)  # 从结构解包所有字段
        x = v2struct(S, 'x')  # 只解包特定字段
    
    参数:
    *args: 变量或结构
    **kwargs: 关键字参数（用于打包）
    
    返回:
    打包模式: 返回字典（结构）
    解包模式: 返回元组或单个值
    """
    if len(args) == 0 and len(kwargs) > 0:
        # 打包模式：使用关键字参数
        return kwargs
    
    elif len(args) == 1 and isinstance(args[0], dict):
        # 解包模式：从字典解包
        struct = args[0]
        if len(kwargs) == 0:
            # 解包所有字段
            return tuple(struct.values())
        else:
            # 解包特定字段
            field_names = kwargs.get('fieldNames', [])
            if isinstance(field_names, str):
                field_names = [field_names]
            return tuple(struct[f] for f in field_names if f in struct)
    
    elif len(args) > 0:
        # 打包模式：使用位置参数
        # 获取调用者的局部变量
        frame = inspect.currentframe().f_back
        caller_locals = frame.f_locals
        
        result = {}
        for i, arg in enumerate(args):
            # 尝试获取变量名
            var_name = None
            for name, value in caller_locals.items():
                if value is arg:
                    var_name = name
                    break
            
            if var_name is None:
                var_name = f'var{i+1}'
            
            result[var_name] = arg
        
        return result
    
    else:
        # 无参数：打包调用者的所有局部变量
        frame = inspect.currentframe().f_back
        caller_locals = frame.f_locals
        
        # 排除特殊变量
        exclude = {'self', '__builtins__', '__name__', '__doc__', '__package__'}
        result = {k: v for k, v in caller_locals.items() if k not in exclude}
        
        return result


def pack_to_struct(**kwargs):
    """
    将关键字参数打包到字典中
    
    参数:
    **kwargs: 关键字参数
    
    返回:
    字典
    """
    return kwargs


def unpack_from_struct(struct, *field_names):
    """
    从字典解包字段
    
    参数:
    struct: 字典
    *field_names: 要解包的字段名
    
    返回:
    如果只有一个字段，返回该值；否则返回元组
    """
    if len(field_names) == 0:
        # 解包所有字段
        return tuple(struct.values())
    elif len(field_names) == 1:
        # 只解包一个字段
        return struct.get(field_names[0])
    else:
        # 解包多个字段
        return tuple(struct.get(f) for f in field_names)

