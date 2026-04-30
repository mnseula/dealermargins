Imports System.Data
Imports System.Data.SqlClient
Imports System.Web.UI.WebControls

Partial Class Workstations_FurniturePickListSouth
    Inherits System.Web.UI.Page

    Public Sub MesgBox(ByVal sMessage As String)
        Dim msg As String
        msg = "<script language='javascript'>"
        msg += "alert('" & sMessage & "');"
        msg += "<" & "/script>"
        Response.Write(msg)
    End Sub

    Protected Sub gvFurniture_RowCommand(sender As Object, e As GridViewCommandEventArgs) Handles gvFurniture.RowCommand

        If e.CommandName = "gotoorderdetails" Then
            Dim SONo As String = e.CommandArgument
            Dim url As String = "../OrderDetails.aspx?SONo=" & SONo
            Response.Write("<script language='javascript'> {popUpObj=window.open ('" & url & "' ,'mywindow','menubar=0,resizable=0,width=900,height=900,toolbars=0');popUpObj.focus()}</script>")
        End If

        If e.CommandName = "gotoupdate2" Then
            Dim Key As String = e.CommandArgument
            Dim SelectedProdNo As Integer = gvFurniture.Rows(Key).Cells(0).Text
            Dim img As Image = CType(gvFurniture.Rows(Key).FindControl("btnUpdateFurniture"), Image)
            Dim floorvalue = img.ImageUrl
            floorvalue = Mid(floorvalue, 26, 1)
            Dim NextWorkstationHasDate As Int16

            Dim conn As New SqlConnection()
            Dim connstr As String = ConfigurationManager.ConnectionStrings("bml_dataConnectionString").ConnectionString

            Dim cmd As New SqlCommand
            Dim cmd2 As New SqlCommand
            Dim cmd3 As New SqlCommand
            Dim cmd4 As New SqlCommand

            Dim TodaysDate As Date = Date.Now
            Dim ThisDay As Date = TodaysDate.Date
            Dim recordcount As Int16 = 0

            conn.ConnectionString = connstr

            cmd.CommandType = CommandType.Text

            cmd.CommandText = "UPDATE BML_POPREPORTING_GREENLIGHTS SET FurnitureInstalledStatus = '2', HelmInstalledStatus = '1', FurnitureInstalled = '" & TodaysDate & "' where ProdNo =  '" & SelectedProdNo & "'"
            cmd2.CommandText = "Select Count (*) FROM BML_POPREPORTING_GREENLIGHTS where FurnitureInstalledStatus = 2 and BuildLoc = 'S' and Convert(date,FurnitureInstalled) ='" & ThisDay & "'"
            cmd3.CommandText = "Select Count (*) FROM BML_POPREPORTING_GREENLIGHTS where HelmInstalled is not NULL and ProdNo = '" & SelectedProdNo & "'"
            cmd4.CommandText = "UPDATE BML_POPREPORTING_GREENLIGHTS SET FurnitureInstalledStatus = '1', HelmInstalledStatus = '0', FurnitureInstalled = NULL where ProdNo =  '" & SelectedProdNo & "' and HelmInstalled is NULL"

            cmd.Connection = conn
            cmd2.Connection = conn
            cmd3.Connection = conn
            cmd4.Connection = conn

            conn.Open()

            If floorvalue <= 1 Then
                cmd.ExecuteNonQuery()
            Else
                NextWorkstationHasDate = Convert.ToInt16(cmd3.ExecuteScalar())
                If NextWorkstationHasDate = 1 Then
                    MesgBox("You cannot undo this action becuase the next station has already completed this boat.")
                Else
                    cmd4.ExecuteNonQuery()
                End If
            End If

            recordcount = Convert.ToInt16(cmd2.ExecuteScalar())
            lblBoatsStarted.Text = recordcount

            gvFurniture.DataBind()
            conn.Close()
        End If

    End Sub

    Protected Sub Page_Load(sender As Object, e As EventArgs) Handles Me.Load
        Dim conn As New SqlConnection()
        Dim connstr As String = ConfigurationManager.ConnectionStrings("bml_dataConnectionString").ConnectionString

        Dim cmd2 As New SqlCommand

        Dim TodaysDate As Date = Date.Now
        Dim ThisDay As Date = TodaysDate.Date
        Dim recordcount As Int16 = 0
        Dim DaystoShow As String

        If ddlDaysInAdvance.Items.Count = 0 Then
            DaystoShow = ThisDay.AddDays(5).ToString("yyyy-MM-dd")
            ddlDaysInAdvance.Items.Add(New ListItem("3 Days", DaystoShow))
            DaystoShow = ThisDay.AddDays(7).ToString("yyyy-MM-dd")
            ddlDaysInAdvance.Items.Add(New ListItem("5 Days", DaystoShow))
            DaystoShow = ThisDay.AddDays(12).ToString("yyyy-MM-dd")
            ddlDaysInAdvance.Items.Add(New ListItem("10 Days", DaystoShow))
            DaystoShow = ThisDay.AddDays(17).ToString("yyyy-MM-dd")
            ddlDaysInAdvance.Items.Add(New ListItem("15 Days", DaystoShow))
            DaystoShow = ThisDay.AddDays(22).ToString("yyyy-MM-dd")
            ddlDaysInAdvance.Items.Add(New ListItem("20 Days", DaystoShow))
        End If

        conn.ConnectionString = connstr
        cmd2.CommandType = CommandType.Text
        cmd2.CommandText = "Select Count (*) FROM BML_POPREPORTING_GREENLIGHTS where FurnitureInstalledStatus = 2 and BuildLoc = 'S' and Convert(date,FurnitureInstalled) ='" & ThisDay & "'"
        cmd2.Connection = conn

        conn.Open()
        recordcount = Convert.ToInt16(cmd2.ExecuteScalar())
        lblBoatsStarted.Text = recordcount
        lblBoatsStarted.Visible = False
        conn.Close()
    End Sub

    Protected Sub btnRefresh_Click(sender As Object, e As EventArgs) Handles btnRefresh.Click
        gvFurniture.DataBind()
    End Sub

    Protected Sub gvFurniture_RowDataBound(sender As Object, e As GridViewRowEventArgs) Handles gvFurniture.RowDataBound
        If e.Row.RowType = DataControlRowType.DataRow Then

            Dim prod As String = e.Row.Cells(0).Text
            prod = Mid(prod, 3)

            Dim s As SqlDataSource = CType(e.Row.FindControl("sdsLocs"), SqlDataSource)
            Try
                s.SelectParameters(0).DefaultValue = prod
            Catch
            End Try

        End If
    End Sub

    Protected Sub locs_RowCommand(sender As Object, e As GridViewCommandEventArgs)
        If e.CommandName = "pullaskid" Then

            Dim Selected As String = Convert.ToString(e.CommandArgument)
            Dim Line() As String = Selected.Split(";")
            Dim SelectedProdNo As Integer = Convert.ToInt16(Line(0))
            Dim LocKey As String = Line(1)
            Dim SelectedNo As String

            Dim conn As New SqlConnection()
            Dim connstr As String = ConfigurationManager.ConnectionStrings("bml_dataConnectionString").ConnectionString
            Dim cmd As New SqlCommand
            conn.ConnectionString = connstr
            cmd.Connection = conn
            SelectedNo = SelectedProdNo.ToString
            SelectedNo = SelectedNo.PadLeft(5, "0")
            cmd.CommandText = "Update Material_Locations Set InUse ='0', ProdNo = Null, DateIn = Null, Rear = 0 where LocKey = '" & LocKey & "' and ProdNo = '" & SelectedNo & "'"

            conn.Open()
            cmd.ExecuteNonQuery()
            conn.Close()
            gvFurniture.DataBind()

        End If
    End Sub

End Class
