class GanZhi:
    """處理干支計算的核心類別"""
    
    # 使用類別常數，方便日後維護
    STREAMS = "甲乙丙丁戊己庚辛壬癸"
    BRANCHES = "子丑寅卯辰巳午未申酉戌亥"  # 增加地支常數

    @classmethod
    def get_full_ganzhi(cls, year: int, month: int, day: int, hour: int) -> str:
        """未來可整合此處計算完整四柱"""
        pass
    
    @classmethod
    def _stem_to_idx(cls, stem: str) -> int:
        """將天干轉換為 0-9 的索引"""
        if stem not in cls.STREAMS:
            raise ValueError(f"無效的天干: {stem}")
        return cls.STREAMS.index(stem)

    @classmethod
    def get_month_gan(cls, year_gan: str, month: int) -> str:
        """
        五虎遁月演算法
        公式推導：年干索引與寅月天干對應關係固定
        """
        if not 1 <= month <= 12:
            raise ValueError("月份須介於 1-12")
            
        # 寅月的天干索引規律
        # 甲己(0, 5) -> 丙(2) | 乙庚(1, 6) -> 戊(4) | ...
        y_idx = cls._stem_to_idx(year_gan)
        start_idx = (y_idx % 5 * 2 + 2) % 10
        
        # 月干計算
        month_gan_idx = (start_idx + month - 1) % 10
        return cls.STREAMS[month_gan_idx]

    @classmethod
    def get_hour_gan(cls, day_gan: str, hour_idx: int) -> str:
        """
        五鼠遁日演算法
        hour_idx: 0(子) - 11(亥)
        """
        if not 0 <= hour_idx <= 11:
            raise ValueError("時辰索引須介於 0-11 (子-亥)")
            
        # 子時的天干索引規律
        d_idx = cls._stem_to_idx(day_gan)
        start_idx = (d_idx % 5 * 2) % 10
        
        # 時干計算
        hour_gan_idx = (start_idx + hour_idx) % 10
        return cls.STREAMS[hour_gan_idx]
