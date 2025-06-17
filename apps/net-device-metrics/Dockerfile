FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

COPY net-device-metrics.csproj ./
RUN dotnet restore

COPY . .

RUN dotnet build "net-device-metrics.csproj" -c Release -o /app/build
RUN dotnet publish "net-device-metrics.csproj" -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app/publish .

ENTRYPOINT ["dotnet", "net-device-metrics.dll"]
