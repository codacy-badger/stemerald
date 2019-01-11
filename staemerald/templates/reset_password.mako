<%inherit file="email_master.mako" />
<tr>
    <td>
        <table class="content" align="center" cellspacing="30px" style="border-bottom: 1px solid black">
            <tr>
                <td align="center">
                    <h2 style="font-size: 18px">Hello, ${receiver}</h2>
                </td>
            </tr>
            <tr align="center">
                <td>
                    <p style="color: rgb(80, 80, 80)">Lorem ipsum dolor sit amet, consectetur adipisicing elit. Aliquid, aperiam atque, consequatur corporis dolor
                        doloremque eos eum impedit, ipsam nesciunt nobis officiis perferendis quisquam sapiente totam veritatis
                        voluptate voluptatem voluptates.</p>
                </td>
            </tr>
            <tr align="center">
                <td bgcolor="#F2F2F2" style="border-radius: 15px; border: 2px solid #dddddd;">
                    <table cellpadding="15px">
                        <tr>
                            <td align="center">
                                <p style="color: rgb(80, 80, 80); font-size: 18px;">Click the below link to reset password!
                                    <a href="${url}?t_=${token}" target="_blank" style="text-decoration: none; color: rgb(56, 207, 252); font-size: 18px;">here</a>.</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </td>
</tr>
