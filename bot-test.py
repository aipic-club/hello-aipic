from snowflake import Snowflake

# will generate a snowflake -> 1414366371759784960
# snowflake = Snowflake(1111174990251962439)
# print(snowflake.to_binary)

#1111212578001911808
snowflake = Snowflake(1111241531920224369)
print(snowflake.to_date)
snowflake = Snowflake(1111240913104928768)
print(snowflake.to_date)
print(snowflake.to_binary)

